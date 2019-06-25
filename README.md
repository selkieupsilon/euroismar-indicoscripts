# euroismar-indicoscripts
Indico scripts for exporting data and various specific tasks, developed for EUROISMAR 2019

Tasks:
* JSON export from Indico for EUROISMAR 2019 abstract book typesetting
  * constructs HTTP API request to Indico for contributions in event
  * remove event nodes that are unnecessary for contributions
  * exports into one combined file
  * exports into separate files split by type of contribution
  * Posters are sorted by board number
  * Talks are sorted by start time
