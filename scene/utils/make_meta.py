import csv
import json
import os

import h5py
import numpy as np

from core import WORKING_DIR

DATA_DIR = os.path.join(WORKING_DIR, 'ShapeNetCore.v1')

# returns a list of synset_ids
def get_synset_ids(taxonomy):
  synset_ids = [0]
  synset_parents = [0]
  for synset in taxonomy:
    synset_ids.append(synset["synsetId"])
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

  assert(len(synset_ids) == len(synset_parents))
  # 2 columns: [ synset_id, idx of the parent synset ]
  return (
    np.asarray(synset_ids, dtype=np.str),
    np.asarray(synset_parents, dtype=np.int),
  )


# returns a list of tags
def get_tags(taxonomy):
  tags = []
  for synset in taxonomy:
    tags.extend(synset["name"].split(","))

  # verify that there are duplicate tags
  assert(len(set(tags)) < len(tags))

  # strip out the nonunique tags
  tag_set = set()
  unique_tags = []
  for tag in tags:
    if tag not in tag_set:
      unique_tags.append(tag)
      tag_set.add(tag)

  # 1 column: [ tag ]
  return (
    np.asarray(unique_tags, dtype=np.str),
  )

def get_synset_tags(taxonomy, tags, synsets_ids):
  synset_id_idx_map = {synset_id: idx for idx, synset_id in enumerate(synset_ids)}
  tag_id_idx_map = {tag: idx for idx, tag in enumerate(tags)}

  synset_idxs, tag_idxs = [], []
  for synset in taxonomy:
    for tag in synset["name"].split(","):
      synset_idxs.append(synset_id_idx_map[synset["synsetId"]])
      tag_idxs.append(tag_id_idx_map[tag])

  return (
    np.asarray(synset_idxs, dtype=np.int),
    np.asarray(tag_idxs, dtype=np.int),
  )


def get_models(synset_ids, synset_parents):
  # synsets at the top of the file directory
  top_level = {x for x in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, x))}
  synset_id_idx_map = {synset_id: idx for idx, synset_id in enumerate(synset_ids)}

  # synsets without parents
  roots = []

  for synset_id, synsetParent in zip(synset_ids[1:], synset_parents[1:]):
    if synsetParent == 0:
      roots.append(synset_id)

  # get the intersection
  mainSynset_ids = [synset_id for synset_id in roots if synset_id in top_level]

  hashes, main_synsets, all_synsets, subtags, ups, fronts, names = [], [], [], [], [], [], []
  for synset_id in mainSynset_ids:
    with open(os.path.join(DATA_DIR, '%s.csv' % synset_id)) as f:
      f.readline()  # skip the headerline
      for row in csv.reader(f, delimiter=',', quotechar='"'):
        fullid, wnsynset, tags, up, front, name, _ = row

        hashes.append(fullid.split('.')[1])
        main_synsets.append(synset_id_idx_map[synset_id])
        all_synsets.append(wnsynset)
        subtags.append(tags)
        ups.append(up)
        fronts.append(front)
        names.append(name)

  return (
    np.asarray(hashes, dtype=np.str),
    np.asarray(main_synsets, dtype=np.int),
    np.asarray(all_synsets, dtype=np.str),
    np.asarray(subtags, dtype=np.str),
    np.asarray(ups, dtype=np.str),
    np.asarray(fronts, dtype=np.str),
    np.asarray(names, dtype=np.str),
  )

def get_model_synsets(model_hashes, model_all_synsets, synset_ids):
  synset_id_idx_map = {synset_id: idx for idx, synset_id in enumerate(synset_ids)}

  model_idxs, synset_idxs = [], []
  for idx, (mhash, synsets) in enumerate(zip(model_hashes, model_all_synsets)):
    for synset_id in synsets.split(','):
      model_idxs.append(idx)
      synset_idxs.append(synset_id_idx_map[synset_id])

  return (
    np.asarray(model_idxs, dtype=np.int),
    np.asarray(synset_idxs, dtype=np.int),
  )


if __name__ == '__main__':
  with open(os.path.join(DATA_DIR, 'taxonomy.json')) as f:
    taxonomy = json.load(f)

  synset_ids, synset_parents = get_synset_ids(taxonomy)
  tags, = get_tags(taxonomy)
  synset_tag_synset_idxs, synset_tag_tag_idxs = get_synset_tags(taxonomy, tags, synset_ids)
  models = get_models(synset_ids, synset_parents)
  model_hashes, main_synsets, all_synsets, subtags, ups, fronts, names = models
  model_synset_model_idxs, model_synset_synset_idxs = get_model_synsets(model_hashes, all_synsets, synset_ids)

  with h5py.File("metadata.hdf5", "w") as f:
    h5_synset_relations = f.create_group("synset_relations")
    h5_synset_relations.create_dataset("ids", data=synset_ids)
    h5_synset_relations.create_dataset("parents", data=synset_parents)

    h5_tags = f.create_group("tags")
    h5_tags.create_dataset("names", data=tags)

    h5_synset_tags = f.create_group("synset_tags")
    h5_synset_tags.create_dataset("synset_idxs", data=synset_tag_synset_idxs)
    h5_synset_tags.create_dataset("tag_idxs", data=synset_tag_tag_idxs)

    h5_models = f.create_group("models")
    h5_models.create_dataset("hashes", data=model_hashes)
    h5_models.create_dataset("main_synsets", data=main_synsets)
    h5_models.create_dataset("ups", data=ups)
    h5_models.create_dataset("fronts", data=fronts)
    h5_models.create_dataset("names", data=names)

    h5_model_synsets = f.create_group("model_synsets")
    h5_model_synsets.create_dataset("model_idxs", data=model_synset_model_idxs)
    h5_model_synsets.create_dataset("synset_idxs", data=model_synset_synset_idxs)
