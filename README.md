# CS310: Analysing data from Twitter Feeds to Determine the Outcome of Football Matches

This project contains the source code and documentation for my third year dissertation project where I attempted to determine the outcome of premier league games using twitter feeds as well as statistical history.

## Set up

1. This set up assumes you have downloaded this package and are in the current directory reading this README.md
2. First step is to install virtualenvwrapper.
3. Then enter ```mkvirtualenv <project_name>``` command replacing <project_name> with a name.
4. Activate this new environment by using the ```source ./<project_name>/bin/activate``` command.
5. Install the required packages using the provided pip: ```./<project_name>/bin/pip -r requirements.txt```.
6. Use the provided python binary to start the server: ```./<project_name>/bin/python run.py```.
7. Navigate to 127.0.0.1:5000 and begin using the project

## Configuration

The config.py file contains API keys to use.

* FOOTBALL_DATA_KEY can be found at: http://www.football-data.org/
* FOOTBALL_API_KEY can be found at: https://football-api.com/
* CROWD_SCORE_KEY can be found at: http://fastestlivescores.com/live-scores-api-feed/
* Twitter keys and secrets can be found at: https://apps.twitter.com/ and creating a new app
* DEBUG is a variable that can be True or False depending on if you want to output logging info to the console

## Project structure

There are three folders.

* The ```data``` folder contains jsons of each team when parsed. This is only created when DEBUG is True as writing to file is expensive in terms of I/O operations.
* The ```static``` folder contains all the assets required to render a HTML page such as CSS, JS, images etc. They can be stored in cache for quicker loading.
* The ```templates``` folder contains each template for each route. Variables are passed to this template which then use data returned by functions to dynamically create the HTML page required.

The bulk of the work comes from the remaining 5 python files.

* The entry point ```run.py``` contains the route. It is the connection between the front-end and backend. Once getting the path from the browser, it uses functions to obtain data which it then bundles into variables to pass to the templates.
* The ```run.py``` file talks to two helper functions. These are ```functions.py``` and ```util.py```. ```util.py``` is more of a look-up dictionary which avoids repeated code and contains utility objects. ```functions.py``` on the other hand helps by doing the calculation before returning the final values to ```run.py```. Most of the API requests which determine the match information come from ```functions.py```.
* ```historic_data.py``` is responsible for collecting match specific data as well as in-depth information on specific teams. It then uses this information to create a score for win, loss or draw.
* ```twitter_data.py``` is similar to ```historic_data.py``` except it anaylses tweets to determine positive and negative scores. However the output is the same as ```historic_data.py``` so that those values can be processed by ```functions.py```.
