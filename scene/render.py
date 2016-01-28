from collections import defaultdict
import os
import random
import subprocess
import zipfile
import re
import shutil
import multiprocessing

from utils import WORKING_DIR

DATA_DIR = os.path.join(WORKING_DIR, 'ShapeNetCore.v1')
OUTPUT_DIR = os.path.join(WORKING_DIR, 'renders')
OUTPUT_SCRIPTS = os.path.join(OUTPUT_DIR, 'scripts')
OUTPUT_IMAGES = os.path.join(OUTPUT_DIR, 'images')
OUTPUT_LOGS = os.path.join(OUTPUT_DIR, 'logs')


data = []
# TODO: get this information from the metadata
for filename in os.listdir(DATA_DIR):
  if not os.path.isdir(os.path.join(DATA_DIR, filename)):
    continue

  synsetID = filename
  data.extend([(synsetID, obj_hash) for obj_hash in os.listdir(os.path.join(DATA_DIR, synsetID))])


class Image(object):
  def __init__(self, filepath, scale=None, pos=None, rot=None, tags=None):
    self.filepath = filepath
    self.scale = scale or (1., 1., 1.)
    self.pos = pos or (0., 0., 0.)
    self.rot = rot or (0., 0., 0.)
    self.tags = tags or []

  @classmethod
  def generate_random(cls):
    # pick a filepath at random
    model = data[random.randint(0, len(data)-1)]
    filepath = os.path.join(DATA_DIR, model[0], model[1], 'model.obj')

    # pick a scale at random
    scale_k = random.randint(1, 4)
    scale = (scale_k, scale_k, scale_k)

    # pick a position at random
    pos = (
      random.normalvariate(0, 2),
      random.normalvariate(0, 2),
      0.0,
    )

    # pick a rotation at random
    rot = (
      random.normalvariate(0, 0.5),
      random.normalvariate(0, 0.5),
      random.random() * 360
    )

    # return the image
    return cls(filepath, scale, pos, rot, [])

  def to_string(self):
    result = "Image(filepath='{filepath}', scale={scale}, pos={pos}, rot={rot})".format(
      filepath=self.filepath,
      scale=self.scale,
      pos=self.pos,
      rot=self.rot,
    )

    return result


def render(args):
  images, img_idx = args
  # write the render python script
  output_filepath = os.path.join(OUTPUT_IMAGES, '%d.png' % img_idx)
  with open('template.txt') as f:
    script = f.read().format(
      images=",\n".join(image.to_string() for image in images),
      output_filepath=output_filepath,
    )
  render_script_filepath = os.path.join(OUTPUT_SCRIPTS, '%d.py' % img_idx)
  with open(render_script_filepath, 'w') as f:
    f.write(script)

  # launch blender
  outfile = open(os.path.join(OUTPUT_LOGS, '%d.out' % img_idx), 'w')

  proc = subprocess.Popen(
    ["blender", "-b", "-P", render_script_filepath],
    stdout=outfile,
    stderr=subprocess.PIPE,
  )
  _, err = proc.communicate()
  outfile.close()

  if err:
    with open(os.path.join(OUTPUT_LOGS, '%d.err' % img_idx), 'w') as f:
      f.write(err)

  # save results into database
  return err


def main(n_renders):
  pool = multiprocessing.Pool(8)
  args = []
  for idx in range(n_renders):
    args.append(([Image.generate_random(), Image.generate_random()], idx))
  errors = pool.map(render, args)

  if any(errors):
    for idx, err in enumerate(errors):
      if err:
        print "Task %d threw an error; you may want to examine the logs" % idx
        # Errors aren't always fatal and sometimes lead to working renders
  else:
    print "All renders succeeded"


if __name__ == '__main__':
  n_renders = multiprocessing.cpu_count()
  main(n_renders)

