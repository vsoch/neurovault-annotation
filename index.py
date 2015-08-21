from flask import Flask, render_template
from pybraincompare.report.colors import random_colors
from hypothesis import HypothesisRawAnnotation
import requests
import json
import pandas

app = Flask(__name__)

def get_annotations(url,column_names):
    url = "https://hypothes.is/api/search?uri=%s" %(url)
    print url
    text = requests.get(url).text.decode('utf-8')
    rows = json.loads(text)['rows']
    raw = [HypothesisRawAnnotation(row) for row in rows]
    print raw
    # We will take the first tag!
    annots = dict()
    # Very simple - will only allow for one annotation per tag
    # Also assumes one tag per annotation
    # We can obviously improve upon this!
    for r in raw:
        if r.tags[0] in column_names:
            annots[r.tags[0]] = r.text
    print annots
    return annots    

def get_collections():
    # Retrieve neurovault images, sort
    pkl = "static/data/nv_collections.pkl"
    collections = pandas.read_pickle(pkl)
    collections = collections[collections["DOI"].isnull()==False]
    
    # Remove more proprietary stuffs
    collections =  collections.drop(["owner","add_date","contributors"],axis=1)
    return collections

@app.route("/annotate/<pk>")
def annotate(pk):
    collections = get_collections()
    # Get annotations for the pk
    url = collections["url"][collections["collection_id"]==int(pk)].tolist()[0]
    annots = get_annotations(url,collections.columns)
    return main_page(collections,annotations=annots)

@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/")
def annotate_nv():
    collections = get_collections()
    return main_page(collections)
 
def main_page(collections,annotations=None):

    print annotations
    # We don't need to annotate these
    not_annotations = ["url","collection_id","DOI"]
    total_annotations = len(collections.columns) - len(not_annotations)
    collections["missing_annotations"] = total_annotations - collections.count(axis=1)
    collections["defined_annotations"] = collections.count(axis=1)

    # Convert (most) columns to strings
    for col in collections.columns:
        try:
            collections[col] =  collections[col].astype(str)
        except:
            pass

    # Fill in nan with None
    collections[collections.isnull()] = None

    # Convert each collection into a dict
    lists = []
    for row in collections.iterrows():
        lists.append(row[1].to_dict())

    # render images with contrasts tagged
    if annotations != None:
        return render_template("index.html",collections=lists,annotations=annotations)
    return render_template("index.html",collections=lists)

if __name__ == "__main__":
    app.debug = True
    app.run()

