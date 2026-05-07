## Setting up this project

### Step 1: Set up database in adult_demo_dataset
I needed to move the database set-up to a separate project so that Claude code didn't try to use the CSVs instead of using the database tables.

1. Open the project `adult_demo_dataset`.
2. In a new terminal window, navigate to the `database` directory and run `docker-compose up`.
3. Run the file `insert-data-into-postgres.py`.
4. Navigate back over to this project. Connect to the database:
   a. User: jetbrains
   b. Password: jetbrains
   c. Database: demo
5. Create primary keys for demographics, education and occupation "id" columns, and create new foreign keys linking these to the "demographics_id", "education_id" and "occupation_id" columns in the person table.

### Step 2: Set up the main project
1. Open `pyproject.toml` and prompt PyCharm to create a new uv environment.

## Demo steps
For best results, run this demo using Claude Agent in "Bypass Permissions" mode and with Opus 4.7.

Depending on what people want to see, there's the option to show:
1. How easily you can create a new project using uv (don't create the project, just show the "New Project" window).
2. How you can use the Python Packages tool window to install packages straight into your uv environment.
3. Show the Database tool window, explain all the supported databases.
4. Show the AI Chat window and the support for different agents, and how this is relatively plug-and-play for the major agents. The set up with skills and agents.md files is the same.
5. Show the project set up for Claude Code in this project, and explain the role of the Claude.md file versus skills.
6. Show the skills manager, and how they're automatically detected by PyCharm.
7. Show /explore_db skill. Ask natural language queries about the data and at the end ask for the following:
> Can you please give me the query to get the full table, including the columns: age, "capital-gain", "capital-loss", "hours-per-week", income, "marital-status", relationship, race, sex, "native-country", education, workclass, occupation
8. Paste this code into the first cell of `cleaning.ipynb`. Change this to a SQL cell, connect it to `demo@localhost` and change the name to `df_raw`.
9. Show how the DataFrame viewer has already allowed us to see several issues using the Column Statistics and Dataset Issues.
10. Show /clean_data skill. Demonstrate how it locates data issues.
