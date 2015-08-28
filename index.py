from flask import Flask, render_template
from hypothesis import HypothesisRawAnnotation
import requests
import numpy
import json
import re
import pandas

app = Flask(__name__)

def get_annotations(urls,column_names):
    if not isinstance(urls,list): urls = [urls]
    annotations = dict()
    for u in urls:
        url = requests.get(u).url
        url = "https://hypothes.is/api/search?uri=%s" %(url)
        text = requests.get(url).text.decode('utf-8')
        rows = json.loads(text)['rows']
        raw = [HypothesisRawAnnotation(row) for row in rows]        
        annots = []        
        for r in raw:
            data = dict()
            # Find tags, and ids
            ids = [id for id in [re.findall("^-?[0-9]+$",tag) for tag in r.tags] if id]
            if ids:
                ids = ids[0]
            else:
                ids = []
            tags = [tag for tag in r.tags if tag not in ids]
            if len(ids)==0: ids = None
            # We are only taking the first id annotation, one image per annotation
            data["image_id"] = ids
            data["tags"] = [{tag:r.text} for tag in tags]
            annots.append(data)
        if len(annots) > 0:
            annotations[u] = annots
    return annotations    

def get_images(pk):
    url = "http://neurovault.org/api/collections/%s/images/?format=json" %pk    
    return json.loads(requests.get(url).text.decode('utf-8'))

def get_collections(pk=None):
    # Retrieve neurovault images, sort
    pkl = "static/data/nv_collections.pkl"
    collections = pandas.read_pickle(pkl)
    collections = collections[collections["DOI"].isnull()==False]
    
    # Remove more proprietary stuffs
    collections =  collections.drop(["owner","add_date","contributors"],axis=1)
    if pk:
        collections = collections[collections.collection_id==int(pk)]
    return collections

# Change nan values to None to render correctly in interface
def nan_to_none(field):
    try:
        if numpy.isnan(field):
            return None
    except:
        pass
    return field

# Important fields
def get_important_fields(images,coll):
    metadata = []
    missing = 0
    present = 0
    for image in images["results"]:
        smoothness = nan_to_none(image["smoothness_fwhm"])
        image_metadata = {"figure":image["figure"],
                         "cognitive_paradigm_cogatlas":image["cognitive_paradigm_cogatlas"],
                         "contrast_definition":image["contrast_definition"],
                         "image_type":image["image_type"],
                         "modality":image["modality"],
                         "name":image["name"],
                         "map_type":image["map_type"],
                         "smoothness_fwhm":smoothness,
                         "thumbnail":image["thumbnail"],
                         "url":image["url"],
                         "id":image["id"]}
        missing += sum(x is None for x in image_metadata.values())
        present += sum(x is not None for x in image_metadata.values())
        metadata.append(image_metadata)

    subjects = nan_to_none(coll["number_of_subjects"].values[0])

    collection = {"coordinate_space":coll["coordinate_space"].values[0],
            "software_package":coll["software_package"].values[0],
            "used_motion_correction":coll["used_motion_correction"].values[0],
            "number_of_subjects":subjects,
            "name":coll["name"].values[0],
            "url":coll["url"].values[0],
            "journal":coll["journal_name"].values[0],
            "authors":coll["authors"].values[0],
            "id":coll["collection_id"].values[0]}

    missing = (sum(x is None for x in collection.values())) + missing
    present = (sum(x is None for x in collection.values())) + present
    collection["missing"] = missing
    collection["present"] = present
    return {"images":metadata,"collection":collection}

# Match annotations to fields
# Defined fields will not be over-written by annotations
# We can only match images to annotations based on imageID tags
def update_fields(annotations,fields):
    annots = annotations.values()[0]
    for annot in annots:
        # An image annotation
        if annot["image_id"] != None:
             idx = [x for x in range(0,len(fields["images"])) if fields["images"][x]["id"] == int(annot["image_id"][0])][0]
             fields["images"][idx] = update_field(annot,fields["images"][idx])
        
        # A collection annotation
        else:
            fields["collection"] = update_field(annot,fields["collection"])
    return fields

# Update a single field
def update_field(annot,fields):
    for group in annot["tags"]:
        for tag,val in group.iteritems():
            try:
                if not fields[tag]:
                    fields[tag] = val
            except:
                pass
    return fields

# 
def update_annotations(url,collection,pk):
    annots = get_annotations(url,collection.columns)
    # Get images using the neurovault API
    images = get_images(pk)
    # Get important image and collection fields
    fields = get_important_fields(images,collection)

    # Match annotations to fields
    if len(annots) == 0:
        annots[url] = [{"image_id":None,
                       "tags":[{"No annotations found!":""}]}] 
    else:
        fields = update_fields(annots,fields)
    return annots,images,fields

# Single collection view
@app.route("/collection/<pk>")
def collection(pk):
    collection = get_collections(pk=pk)
    # Get annotations for the pk
    url = collection["url"].tolist()[0]
    annots,images,fields = update_annotations(url,collection,pk)
    return render_template("collection.html",
                           images=images,
                           annotations=annots,
                           fields=fields)

# Show annotations for a collection
@app.route("/annotate/<pk>")
def annotate(pk):
    collections = get_collections()
    collection = get_collections(pk)
    # Get annotations for the pk
    url = collection["url"].tolist()[0]
    annots = get_annotations(url,collection.columns)
    annots,images,fields = update_annotations(url,collection,pk)
    return main_page(collections,annotations=annots,fields=fields)

@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/")
def annotate_nv():
    collections = get_collections()
    return main_page(collections)
 
def main_page(collections,annotations=None,fields=None):

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
        return render_template("index.html",collections=lists,annotations=annotations,fields=fields)
    return render_template("index.html",collections=lists)

if __name__ == "__main__":
    app.debug = True
    app.run()

