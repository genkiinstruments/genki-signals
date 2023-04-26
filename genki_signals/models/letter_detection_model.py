import torch
from torch import nn, Tensor
from torch.nn import functional as F
import pytorch_lightning as pl
import torchmetrics


class Scaler(pl.LightningModule):
    def __init__(self, mean, standard_dev):
        super().__init__()
        self._mean = Tensor(mean)
        self._standard_dev = Tensor(standard_dev)

    def forward(self, x: Tensor) -> Tensor:
        return (x - self._mean) / self._standard_dev


class SimpleGruModel(pl.LightningModule):
    def __init__(self, input_size, hidden_size, output_size, lr, scaler_mean, scaler_std):
        super().__init__()
        self.gru = nn.GRU(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        self.hidden_size = hidden_size
        self.lr = lr
        self.loss_func = nn.CrossEntropyLoss()
        self.scaler = Scaler(scaler_mean, scaler_std)
        self.val_acc = torchmetrics.Accuracy(num_classes=output_size, mdmc_average="global")
        self.save_hyperparameters()

    def forward(self, x, h0=None):
        x = self.scaler(x).float()
        out, h0 = self.gru(x, h0)
        out = self.fc(out)
        return out, h0

    def step(self, batch, batch_idx=None):
        x, y = batch
        x = x.float()
        y = y.float()
        y_hat, _ = self.forward(x)
        loss = self.loss_func(y_hat.permute(0, 2, 1), y.permute(0, 2, 1))
        return {
            "loss": loss,
            "y_hat": y_hat.detach().argmax(dim=-1),
            "targets": y.detach().argmax(dim=-1),
        }

    def training_step(self, batch, batch_idx=None):
        outputs = self.step(batch, batch_idx)
        self.log("train_loss", outputs["loss"])
        return outputs["loss"]

    def validation_step(self, batch, batch_idx=None):
        outputs = self.step(batch, batch_idx)
        self.log("val_loss", outputs["loss"])
        self.val_acc.update(outputs["y_hat"], outputs["targets"])
        return outputs["loss"]

    def validation_epoch_end(self, outputs):
        self.log("val_acc", self.val_acc.compute())
        self.val_acc.reset()

    @torch.no_grad()
    def inference(self, x, state=None):
        y_hat, state = self.forward(x, state)
        return F.softmax(y_hat, dim=-1), state

    def configure_optimizers(self):
        opt = torch.optim.Adam(self.parameters(), lr=self.lr)
        scheduler = torch.optim.lr_scheduler.LambdaLR(opt, lambda epoch: 0.99**epoch)
        return [opt], [scheduler]
