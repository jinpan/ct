import csv
import json
import os

import h5py
import numpy as np
import pandas as pd

from core import WORKING_DIR

DATA_DIR = os.path.join(WORKING_DIR, 'ShapeNetCore.v1')

# returns a list of synset_ids
def get_synsets(taxonomy):
  synset_ids = [0]
  synset_names = [""]
  synset_instances = [0]
  synset_parents = [0]
  for synset in taxonomy:
    synset_ids.append(synset["synsetId"])
    synset_names.append(synset["name"])
    synset_instances.append(synset["numInstances"])
    synset_parents.append(0)

  # label parents
  for idx1, parent_synset in enumerate(taxonomy):
    parent_synset_idx = idx1+1

    for idx2, child_synset in enumerate(taxonomy):
      child_synset_idx = idx2+1
      if child_synset["synsetId"] in parent_synset["children"]:
        # verify that each parent is unique
        assert(synset_parents[child_synset_idx] == 0)
        synset_parents[child_synset_idx] = parent_synset_idx

  return pd.DataFrame({
    "id": np.asarray(synset_ids, dtype=np.str),
    "name": np.asarray(synset_names, dtype=np.str),
    "instance": np.asarray(synset_instances, dtype=np.int),
    "parent": np.asarray(synset_parents, dtype=np.int),
  })


def get_models(synset):
  # synsets at the top of the file directory
  top_level = {x for x in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, x))}
  synset_id_idx_map = {synset_id: idx for idx, synset_id in enumerate(synset.id)}

  # synsets without parents
  roots = synsets[(synsets.parent==0)&(synset.id>0)]

  # get the intersection
  mainSynset_ids = [synset_id for synset_id in roots if synset_id in top_level]

  ids = []
  hashes = []
  names = []
  primary_synset_ids = []
  primary_synset_names = []
  synsets_id = []
  synsets_names = []
  ups = []
  fronts = []

  my_id = 0
  for synset_id in mainSynset_ids:
    with open(os.path.join(DATA_DIR, '%s.csv' % synset_id)) as f:
      f.readline()  # skip the headerline
      for row in csv.reader(f, delimiter=',', quotechar='"'):
        fullid, wnsynset, tags, up, front, name, _ = row

        ids.append(my_id)
        hashes.append(fullid.split('.')[1])
        primary_synset_ids.append(synset_id)
        primary_synset_names.append("asdf")
        synsets_id.append(wnsynset)
        synsets_names.append(tags)
        ups.append(up)
        fronts.append(front)
        names.append(name)

        my_id += 1

  return pd.DataFrame({
    "id": np.asarray(ids, dtype=np.int),
    "hash": np.asarray(hashes, dtype=np.str),
    "name": np.asarray(names, dtype=np.str),
    "primary_synset_id": np.asarray(primary_synset_ids, dtype=np.int),
    "primary_synset_name": np.asarray(primary_synset_names, dtype=np.str),
    "synsets_id": np.asarray(synsets_id, dtype=np.str),
    "synsets_names": np.asarray(synsets_names, dtype=np.str),
    "ups": np.asarray(ups, dtype=np.str),
    "fronts": np.asarray(fronts, dtype=np.str),
  })



if __name__ == '__main__':
  with open(os.path.join(DATA_DIR, 'taxonomy.json')) as f:
    taxonomy = json.load(f)

  synsets = get_synsets(taxonomy)
  synsets.to_hdf("metadata.hdf5", "synsets")

  models = get_models(synsets)
  models.to_hdf("metadata.hdf5", "models")

