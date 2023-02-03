import pytorch_lightning as pl
import torch
import torch.nn.functional as F
import wandb
from more_itertools import zip_equal
from torch import nn, Tensor
from torchmetrics import Accuracy, ConfusionMatrix, MatthewsCorrCoef
from torchmetrics.wrappers import MultioutputWrapper

from signal_processing.fft_ops import SpectrogramFeaturesTorch


class StateGruInferenceOnly(pl.LightningModule):
    """A stripped down version of `StateGru` for inference

    This model is an intermediate step moving from scikit-learn + numpy + torch to pure torch

    NOTE: For now model is found at `gs://genki-data/is_touching_models/is_touching.ckpt`

    TODO: Consolidate both models
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        num_layers: int,
        win_size: int,
        hop_len: int,
        fs: int,
        classes: list[str, ...],
        scaler_mean: Tensor,
        scaler_std: Tensor,
        use_softmax: bool = False,
        export: bool = False,
    ):
        super().__init__()
        self.win_size = win_size
        self.fs = fs
        self.classes = classes
        self.hidden_dim = hidden_dim
        # Not sure this belongs here since it's not used, but it's an important hyperparameter that needs to be stored
        self.hop_len = hop_len

        self.rnn = nn.GRU(
            input_size=input_dim,
            hidden_size=self.hidden_dim,
            num_layers=num_layers,
            batch_first=True,
        )
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.normalization = nn.Softmax(dim=-1) if use_softmax else nn.Identity()
        self.relu = nn.ReLU()

        self.scaler = Scaler(mean=scaler_mean, standard_dev=scaler_std)
        self.sp_features = SpectrogramFeaturesTorch(
            self.win_size,
            self.fs,
            detrend_mode="linear",
            fft_type="matrix",
            log=True,
            export=export,
        )

        self._state = None
        self.save_hyperparameters()

    def forward(self, x, prev_state=None):
        out = self.sp_features(x)
        out = self.scaler(out)

        out, state = self.rnn(
            out, prev_state
        )  # out.shape = (batch_size, seq_len, hidden_dim)
        out = self.relu(out)
        out = self.fc(out)  # out.shape = (batch_size, seq_len, output_dim)
        out = self.normalization(out)
        return out, state

    def predict(self, x):
        """Used to predict on new data"""
        y_pred, self._state = self.forward(x.float(), self._state)
        return y_pred
