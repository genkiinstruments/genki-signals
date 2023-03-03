# README
This repo consists of two servers
* a backend which emits data from the genkiML signal system via websockets
* a frontend which receives said data and creates realtime line charts / bar charts / etc.

To run said servers locally you will need the 'genki' conda environment (installation detailed in the wave_ml repo) and npm.

1. Activate the 'genki' environment
2. Run ``` python push_server.py ```
3. Navigate to the `/genki-signals` folder
4. Install the dependencies by running ``` npm i ```
5. Finally run ``` npm run dev ``` which opens the frontend in your default browser ( seems to work best with Firefox currently )
###