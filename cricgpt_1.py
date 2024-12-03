from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.chains import create_sql_query_chain
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate
import os
import getpass
import sqlite3
import pandas as pd
import streamlit as st

# # #load data
# matches = pd.read_csv("matches_cleaned.csv")
# ball_by_ball = pd.read_csv("ballByBall_cleaned_3.csv")
# overs_phase =pd.read_csv("overs_phase.csv")
#print (matches.columns)
#connect to sqlite db
connection = sqlite3.connect('ipl_database.db')
#send to database
# matches.to_sql('Matches',connection,if_exists='replace')
# ball_by_ball.to_sql('ballByBall',connection,if_exists = 'replace')
# overs_phase.to_sql('Overs',connection,if_exists = 'replace')
connection.close()


def cricgpt(prompt):
    openai_api_key = st.secrets["openai_api_key"]
    os.environ["OPENAI_API_KEY"]  = openai_api_key

    db = SQLDatabase.from_uri("sqlite:///ipl_database.db")
    examples = [
        {
            "input" : "How many matches were played in the 2020 season?",
            "query": "SELECT COUNT(*) FROM MATCHES WHERE SEASON = 2020;",
            "result": "[(60,)]",
            "answer": "There were 60 matches played in the 2020 Season"
        },

        {
            "input" : "How many runs has Virat Kohli scored since 2020",
            "query": " SELECT SUM(batsman_run) FROM ballByBall join matches on ballbyball.id = matches.id WHERE batter like '%V%Kohli%' and season >= 2020;",
            "result": "[(1217,)]",
            "answer": "V Kohli has scored 1217 runs since the 2020 season."
        },

        {
            "input" : "How many wickets did Shami take in 2022?",
            "query": " SELECT SUM(bowler_wicket) FROM ballByBall join matches on ballbyball.id = matches.id where bowler like '%M%Shami%' and season = 2022",
            "result": "(21,)",
            "answer": "Mohammed Shami took 21 wickets in 2022."
        },
        {
            "input" : "Who has taken most wickets in the powerplay overs since 2016?",
            "query": " select sum(bowler_wicket),bowler from ballByBall A join Matches B on A.id=B.id join Overs O on A.overs = O.overs where O.phase = 'Powerplay' and season >=2016 group by 2 order by 1 desc limit 1;",
            "result": "(46, 'DL Chahar')",
            "answer": "The top wicket takers since 2016 in the powerplay is DL Chahar with 46 wickets"
        },

        {
            "input" : "Which player has hit most sixers in the death overs since 2020?",
            "query": """ select batter, sum(is_six) as total_sixers
        from ballbyball A join matches B on A.id = B.id
        join Overs O on A.Over_number = O.Overs
        where phase = "Death" and season>=2020 
        group by batter
        order by total_sixers desc limit 1""",
            "result": "('KA Pollard', 36)",
            "answer": "KA Pollard has hit most sixers in the death overs since 2020 with 36 sixers."
        },

        {
            "input" : "Which batter has the highest strike rate? Consider a minimum of 500 balls played.",
            "query" : """select batter,runs, balls_faced, strike_rate from
                        (
                            select batter,sum(batsman_run) as runs, count(*) as balls_faced, (sum(batsman_run) * 100)/count(*) as strike_rate from ballbyball A group by batter
                        ) A

                        where A. balls_faced > 500
                        order by strike_rate desc limit 1;""",
            "result" : "('AD Russell', 2039, 1212, 168)",
            "answer" : "AD Russell has the best strike rate with 168. He has hit 2039 runs in 1212 balls"
        },
        {
            "input" : "Which bowler has the best economy rate in the middle overs since 2016? Consider a minimum of 200 balls bowled?",
            "query" : """select bowler,runs_conceded, balls, economy_rate from
                        (
                                select bowler,sum(total_run) as runs_conceded, count(*) as balls, round(cast(sum(total_run) as real) * 6/count(*),2) as economy_rate from
                                ballbyball A join Overs O on A.Over_number = O.Overs join Matches M on A.id = M.id
                                where O.phase = 'Middle' and season >=2016 group by bowler
                            ) A
                            where A. balls > 200
                            order by economy_rate limit 1;""",
            "result" : "('Rashid Khan', 1662, 1638, 6.09)",
            "answer" : "Rashid Khan has the best economy rate in the middle overs since 2016 with 6.09. He has bowled 1638 balls and conceded 1662 runs."
        },

        {
            "input" : "Give me the total runs scored by Russell team wise?",
            "query" : "select batter, battingteam, sum(batsman_run) from ballbyball where batter like '%Russell%' group by 1,2",
            "result" : """('AD Russell', 'Delhi Daredevils', 58)
                        ('AD Russell', 'Kolkata Knight Riders', 1981)""",
            "answer" : "AD Russell has scored 58 runs for Delhi Daredevils and 1981 runs for Kolkata Knight Riders"
        },

        {
            "input" : "Kohli vs Bumrah matchup",
            "query" : """select batter,sum(batsman_run) as runs,
                        count(*) as balls_faced, 
                        (sum(batsman_run) * 100)/count(*) as strike_rate,
                        sum(bowler_wicket) as Dismissals,
                        sum(is_four) as Fours,
                        sum(is_six) as Sixes
                        from ballbyball A 
                        where batter like '%Kohli%' and bowler like '%Bumrah%'
                        group by 1""",
            "result" : """('V Kohli', 145, 95, 152, 4, 16, 5)""",
            "answer" : """
                Kohli vs Bumrah

                Runs 145
                Balls Faced 95
                Strike rate 152
                Dismissals 4
                Fours 16
                Sixes 5
            """
        }

    ]

    example_prompt = PromptTemplate(
        input_variables=["input", "query", "result", "answer",],
        template="\nQuestion: {input}\nSQLQuery: {query}\nSQLResult: {result}\nAnswer: {answer}",
    )

    from langchain_community.vectorstores import FAISS
    from langchain_core.example_selectors import SemanticSimilarityExampleSelector
    from langchain_openai import OpenAIEmbeddings

    example_selector = SemanticSimilarityExampleSelector.from_examples(
        examples,
        OpenAIEmbeddings(),
        FAISS,
        k=5,
        input_keys=["input"],
    )

    from langchain.prompts import FewShotPromptTemplate
    from langchain.chains.sql_database.prompt import PROMPT_SUFFIX, _mysql_prompt

    #print(PROMPT_SUFFIX)

    new_prompt = """You are a SQLite expert. Given an input question, create a syntactically correct SQLite query to run. 
    Use the Matches database to get details of the season, teams, venue and winning teams.

    Consider the following terms and their calculations when mentioned in a prompt:

    1) Strike Rate - Runs Scored * 100 / Balls faced
    2) Economy rate - Runs CONCEDED * 6 / Balls bowled

    Below are a number of examples of questions and their corresponding SQL queries.

    """

    custom_suffix = """
                Filter the records based on similar or close match. Use the LIKE function when looking for batter or bowler.
            """

    few_shot_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=example_prompt,
        prefix= new_prompt,
        suffix=PROMPT_SUFFIX, 
        input_variables=["input", "table_info", "top_k"], #These variables are used in the prefix and suffix
    )

    from langchain.chains import create_sql_query_chain
    from langchain_openai import ChatOpenAI

    
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature="0")
    local_chain = SQLDatabaseChain.from_llm(llm, db, prompt=few_shot_prompt, use_query_checker=False, 
                                        verbose=True, return_sql=False)
    val = local_chain.invoke(prompt)
    output = val['result']
    return output


