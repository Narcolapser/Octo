# bookish-octo-computing-machine
a uPortal utility program that I wrote because I'm going batty with all these greppings!

Features working:
*	Load servers and authentication from file
*	Connect to servers and display available logs
*	Define what logs you are interested in by entering them into the config file.
*	Filter contents of the logs
*	Download Log file
*	Download Multiple Log Files
*	Copy selected section of log file.
*	Fix threading so the UI doesn't freeze when the treeview is being populated.

Features to work on:
*	Nest logs: there are instances of the same log for different days. I'd like to
		nest these so they are all available, but still compact.
*	Add logfiles dynamically
*	Add servers dynamically
*	Fix filters to leverage the SQL backend
*	Zip Files before downloading

Some dream features:
*	Edit logging files to turn certain logs on and off
*	Re-deploy Portlets

