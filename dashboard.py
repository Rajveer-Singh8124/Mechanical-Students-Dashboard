from flask import Flask, render_template, request, jsonify
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
import math
import os
from dotenv import load_dotenv

load_dotenv()

database = os.getenv("DATABASE")

app = Flask(__name__)


from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = f"mongodb+srv://rajveer:{database}@college.wag2u.mongodb.net/?retryWrites=true&w=majority&appName=College"


client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


db = client["GECA"]
collection = db["Mechanical"]




def extract_student_data(fetch_data):
    
    names = []
    sem1_sgpa = []
    sem2_sgpa = []
    roll_numbers = []
    
    for student in fetch_data:
        names.append(student["name"])
        
        sem1_sgpa.append(float(student["semesters"]["Semester 1"]["SGPA"]))
        sem2_sgpa.append(float(student["semesters"]["Semester 2"]["SGPA"]))
        roll_numbers.append(student["rollno"])
    
    return names, sem1_sgpa, sem2_sgpa, roll_numbers



def compute_cgpa(df):
   
    df_valid = df[(df["Semester 1"] != 0) & (df["Semester 2"] != 0)].copy()
    
    
    df_valid["cgpa"] = (df_valid["Semester 1"] + df_valid["Semester 2"]) / 2 + 0.005
    
    
    df_valid["cgpa"] = df_valid["cgpa"].apply(lambda x: math.trunc(x * 100) / 100.0)
    return df_valid

def get_sgpa_statistics(df):
    
    stats = {}
    sem1_nonzero = df[df["Semester 1"] != 0]["Semester 1"]
    sem2_nonzero = df[df["Semester 2"] != 0]["Semester 2"]
    
    stats["Semester 1"] = {
        "max": sem1_nonzero.max(),
        "min": sem1_nonzero.min(),
        "mean": sem1_nonzero.mean(),
        "len":len(sem1_nonzero)
    }
    stats["Semester 2"] = {
        "max": sem2_nonzero.max(),
        "min": sem2_nonzero.min(),
        "mean": sem2_nonzero.mean(),
        "len":len(sem2_nonzero)
    }
    return stats



def create_subject_grade_dataframe(fetch_data, student_names):
    
    sem1_subjects = [subj["subject"] for subj in fetch_data[0]["semesters"]["Semester 1"]["subjects"]]
    sem2_subjects = [subj["subject"] for subj in fetch_data[0]["semesters"]["Semester 2"]["subjects"]]
    
    
    sem1_grades = []
    sem2_grades = []
    for student in fetch_data:
        grades_sem1 = [subj["grade"] for subj in student["semesters"]["Semester 1"]["subjects"]]
        grades_sem2 = [subj["grade"] for subj in student["semesters"]["Semester 2"]["subjects"]]
        sem1_grades.append(grades_sem1)
        sem2_grades.append(grades_sem2)
    
    
    combined_grades = [g1 + g2 for g1, g2 in zip(sem1_grades, sem2_grades)]
    
    
    sem1_columns = [('Semester 1', subject) for subject in sem1_subjects]
    sem2_columns = [('Semester 2', subject) for subject in sem2_subjects]
    columns = pd.MultiIndex.from_tuples(sem1_columns + sem2_columns, names=['Semester', 'Subject'])
    
    
    df_grades = pd.DataFrame(combined_grades, index=student_names, columns=columns)
    return df_grades



def filter_students_by_grade(df, subjects_to_filter, grades_to_filter):
    
    mask = pd.Series(True, index=df.index)
    for subj in subjects_to_filter:
        
        matching_cols = [col for col in df.columns if col[1] == subj]
        if matching_cols:
           
            condition = df[matching_cols].isin(grades_to_filter).any(axis=1)
            mask = mask & condition
        else:
            
            mask = mask & False  
    return df[mask]


def fetch_subject():
    subject_list = []
    for i in range(len(df_subjects.columns)):
        subject_list.append (df_subjects.columns[i][1])

    return subject_list




fetch_data = list(collection.find({}))


names, sem1_sgpa, sem2_sgpa, roll_numbers = extract_student_data(fetch_data)

students = names

df_sgpa = pd.DataFrame({
    "Name": names,
    "Semester 1": sem1_sgpa,
    "Semester 2": sem2_sgpa
}, index=names)



sem1_rank = df_sgpa["Semester 1"].sort_values(ascending=False)
sem2_rank = df_sgpa["Semester 2"].sort_values(ascending=False)

sem1_rank = sem1_rank.reset_index()
i = sem1_rank[sem1_rank["Semester 1"] ==0].index
sem1_rank.drop(i,inplace=True)


sem2_rank = sem2_rank.reset_index()
i = sem2_rank[sem2_rank["Semester 2"] ==0].index
sem2_rank.drop(i,inplace=True)



pass_df = compute_cgpa(df_sgpa)
cgpa_rank = pass_df["cgpa"].sort_values(ascending=False).reset_index()
cgpa_stats = {
    "min":pass_df["cgpa"].min(),
    "max":pass_df["cgpa"].max(),
    "mean":pass_df["cgpa"].mean(),
    "length":len(pass_df)
}



sgpa_stats = get_sgpa_statistics(df_sgpa)


df_subjects = create_subject_grade_dataframe(fetch_data, names)






def assign_colors(cgpa_list):
   
    return [
        "#2CB536" if c >= 9 else 
        "#5592F7" if c >= 8 else 
        "#FFBA0D" if c >= 7 else 
        "#FF751C" if c >= 6 else
        "#E00D1C"
        for c in cgpa_list
    ]



grade_list  = ["A++","A+","A","B+","B","C+","C","D+","D","E+","E","F"]


df_melted = df_sgpa.melt(
    id_vars=['Name'], 
    value_vars=['Semester 1', 'Semester 2'],
    var_name='Semester', 
    value_name='Score'
)

sem1_fig = px.bar(
    sem1_rank,x="index",y="Semester 1", title="Class Performance of Semester 1",labels={
        "index":"Name of Students","Semester 1":"SGPA"
    }
)
sem1_fig.update_layout(paper_bgcolor="rgb(0,0,0,0)",autosize=True)

sem2_fig = px.bar(
    sem2_rank,x="index",y="Semester 2", title="Class Performance of Semester 2",labels={
        "index":"Name of Students","Semester 2":"SGPA"
    }
)
sem2_fig.update_layout(paper_bgcolor="rgb(0,0,0,0)",autosize=True)


cgpa_fig = px.bar(
    cgpa_rank,x="index",y="cgpa", title="Overall Performance ",labels={
        "index":"Name of Students","cgpa":"CGPA"
    } 
)


both_sem = px.bar(
    df_melted,
    x='Name',
    y='Score',
    color='Semester',
    barmode='group',
    title="Class Performance Across Semesters"
)
both_sem.update_layout(xaxis_tickangle=45, autosize=True)  

def get_figures(selected_student):
    
    student_data = df_sgpa[df_sgpa["Name"] == selected_student].iloc[0]
    
    
    fig1 = go.Figure(
        data=go.Bar(
            x=["First Semester", "Second Semester"],
            y=[student_data["Semester 1"], student_data["Semester 2"]],
            marker_color=assign_colors([student_data["Semester 1"], student_data["Semester 2"]]),
            text=[f"{student_data['Semester 1']:.2f}", f"{student_data['Semester 2']:.2f}"],
            textposition="outside"
        )
    )
    
    
    fig1.update_layout(
        title=f"CGPA Performance of {selected_student}",
        xaxis_title="Semesters",
        yaxis_title="CGPA",
        yaxis=dict(range=[0, 10]),
        width=500
    )
    return fig1

def individual_student_data(name):
    subject_list = []
    grade = list(df_subjects.loc[(name)].values)
    for i in range(len(grade)):
        subject_list.append (df_subjects.columns[i][1])
 
    return subject_list,grade


@app.route('/')
def dashboard():
    
    return render_template("dashboard.html",
                            students=students,
                            sem1_fig=sem1_fig.to_json(),
                            sem2_fig=sem2_fig.to_json(),
                            cgpa_fig=cgpa_fig.to_json(),
                            both_sem = both_sem.to_json(),
                            sgpa_stats=sgpa_stats,
                            cgpa_stats=cgpa_stats,
                            )

@app.route('/selected_student')
def selected_student():
   
    selected_student_name = request.args.get('student')
    
    student_data,student_grade = individual_student_data(selected_student_name)
    return jsonify({"subjects": student_data,"grades":student_grade})




@app.route("/individual_performance")
def individual_performance():
    return render_template("individual_performance.html",students=students)


@app.route("/subject_wise_performance")
def subject_wise_performance():
    subject_list = fetch_subject()
    return render_template("subject_wise_performance.html",subject_list=subject_list,grade_list=grade_list)


@app.route("/subject_grade_data")
def subject_grade_data():
    
    subjects_to_filter=request.args.getlist('subject[]')
    grades_to_filter = request.args.getlist('grade[]')
    filtered_students = filter_students_by_grade(df_subjects, subjects_to_filter, grades_to_filter)
    return jsonify(list(filtered_students.index))


if __name__ == '__main__':
    app.run()




