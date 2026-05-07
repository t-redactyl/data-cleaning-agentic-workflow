import pandas as pd
from sqlalchemy import create_engine

person = pd.read_csv("adult_person.csv", header=0)
occupation = pd.read_csv("adult_occupation.csv", header=0)
demographics = pd.read_csv("adult_demographics.csv", header=0)
education = pd.read_csv("adult_education.csv", header=0)

engine = create_engine("postgresql://jetbrains:jetbrains@localhost/demo")
person.to_sql("person", con=engine)
occupation.to_sql("occupation", con=engine)
demographics.to_sql("demographics", con=engine)
education.to_sql("education", con=engine)
