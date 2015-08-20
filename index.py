from flask import Flask, render_template
from pybraincompare.report.colors import random_colors
import pandas

app = Flask(__name__)

@app.route("/")
def annotate_nv():

    # Retrieve neurovault images, sort
    pkl = "static/data/nv_collections.pkl"
    collections = pandas.read_pickle(pkl)
    collections = collections[collections["DOI"].isnull()==False]
    
    # Convert each collection into a dict
    lists = []
    for row in collections.iterrows():
        lists.append(row[1].to_dict())

    # Generate a color for each task
    #tasks = images["cognitive_paradigm_cogatlas"].unique()
    #num_contrasts = len(tasks)
    #colors = random_colors(num_contrasts)
    #color_lookup = dict()
    #for c in range(0,len(colors)):
    #    color_lookup[tasks[c]] = colors[c]
    #colorvector = [color_lookup[x] for x in images.cognitive_paradigm_cogatlas.tolist()]
    #images["color"] = colorvector

    #TODO: make d3 that will cluster?
    # http://vbmis.com/bmi/project/myconnectome/portal.html
    #TODO: make URL that can show scatterplot or other vis!

    # Prepare variables for context
    #names = images["name"].tolist()
    #contrasts = images["contrast_definition"].tolist()
    #tasks = images["cognitive_paradigm_cogatlas"].tolist()
    #urls = images["url"].tolist()
    #colors = images["color"].tolist()
    #thumbnails = images["thumbnail"].tolist()
 
    # render images with contrasts tagged
    return render_template("index.html",collections=lists)#,context=zip(names,contrasts,tasks,urls,colors,thumbnails))

if __name__ == "__main__":
    app.debug = True
    app.run()

