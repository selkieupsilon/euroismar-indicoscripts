# euroismar-indicoscripts
Python scripts for exporting data from and performing various specific tasks with the Indico conference management system.
Developed for EUROISMAR 2019 http://www.euroismar2019.org/

Tasks:

getcontribsJson.py
* JSON export from Indico for EUROISMAR 2019 abstract book typesetting
  * constructs HTTP API request to Indico for contributions in event
  * removes event nodes that are unnecessary for contributions
  * exports into one combined file
  * exports into separate files split by type of contribution
  * Posters are sorted by board number
  * Talks are sorted by start time
  * Parallel sessions are sorted first by room, then by start time

getsessionsJson.py
* JSON export from Indico for EUROISMAR 2019 abstract book typesetting - program pages
  * constructs HTTP API request to Indico for sessions in event
  * removes event nodes that are unnecessary for sessions
  * sort sessions by room and time
  * simplify JSON to what is necessary for the program pages
