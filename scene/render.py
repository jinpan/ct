from collections import defaultdict
import os
import random
import subprocess
import zipfile
import re
import shutil
import multiprocessing
import time

from utils.core import WORKING_DIR

DATA_DIR = os.path.join(WORKING_DIR, 'ShapeNetCore.v1')
OUTPUT_DIR = os.path.join(WORKING_DIR, 'renders')
OUTPUT_SCRIPTS = os.path.join(OUTPUT_DIR, 'scripts')
OUTPUT_IMAGES = os.path.join(OUTPUT_DIR, 'images')
OUTPUT_LOGS = os.path.join(OUTPUT_DIR, 'logs')

OCCLUSION_NONE = 1
OCCLUSION_LIGHT = 2
OCCLUSION_HEAVY = 3
OCCLUSION_FULL = 4


data = []
# TODO: get this information from the metadata
for filename in os.listdir(DATA_DIR):
  if not os.path.isdir(os.path.join(DATA_DIR, filename)):
    continue

  synsetID = filename
  data.extend([(synsetID, obj_hash) for obj_hash in os.listdir(os.path.join(DATA_DIR, synsetID))])


class Image(object):
  def __init__(self, filepath, scale=None, pos=None, rot=None):
    self.filepath = filepath
    self.scale = (scale, scale, scale) if scale else (1., 1., 1.)
    self.pos = pos or (0., 0., 0.)
    self.rot = rot or (0., 0., 0.)

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
    return cls(filepath, scale, pos, rot)

  @classmethod
  def generate_foreground_background(cls, occlusion):
    f_model = data[random.randint(0, len(data)-1)]
    f_filepath = os.path.join(DATA_DIR, model[0], model[1], 'model.obj')
    f_scale = 7.
    f_rot = (
      random.normalvariate(0, 0.5),
      random.normalvariate(0, 0.5),
      random.random() * 360
    )

    b_model = data[random.randint(0, len(data)-1)]
    b_filepath = os.path.join(DATA_DIR, model[0], model[1], 'model.obj')
    b_scale = 10.
    b_rot = (
      random.normalvariate(0, 0.5),
      random.normalvariate(0, 0.5),
      random.random() * 360
    )

    if occlusion == OCCLUSION_NONE:
      if random.choice((0, 1)):
        y1, y2 = 3., -3.
      else:
        y1, y2 = -3., 3.
    else if occlusion == OCCLUSION_LIGHT:
      while True:
        y1, y2 = random.normalvariate(0, 2), random.normalvariate(0, 2)
        if abs(y1-y2) > 2: break
    else if occlusion == OCCLUSION_HEAVY:
      while True:
        y1, y2 = random.normalvariate(0, 2), random.normalvariate(0, 2)
        if abs(y1-y2) < 2: break
    else if occlusion == OCCLUSION_FULL:
      y1, y2 = 0., 0.

    f_pos = (4., y1, 0.)
    b_pos = (-5., y2, 0.)
    foreground = cls(f_filepath, f_scale, f_pos, f_rot)
    background = cls(b_filepath, b_scale, b_pos, b_rot)

    return foreground, background


  def to_string(self):
    result = "Image(filepath='{filepath}', scale={scale}, pos={pos}, rot={rot})".format(
      filepath=self.filepath,
      scale=self.scale,
      pos=self.pos,
      rot=self.rot,
    )

    return result


def render(args):
  images, img_name = args
  # write the render python script
  output_filepath = os.path.join(OUTPUT_IMAGES, '%s.png' % img_name)
  with open('template.txt') as f:
    script = f.read().format(
      images=",\n".join(image.to_string() for image in images),
      output_filepath=output_filepath,
    )
  render_script_filepath = os.path.join(OUTPUT_SCRIPTS, '%s.py' % img_name)
  with open(render_script_filepath, 'w') as f:
    f.write(script)

  # launch blender
  outfile = open(os.path.join(OUTPUT_LOGS, '%s.out' % img_name), 'w')

  proc = subprocess.Popen(
    ["blender", "-b", "-P", render_script_filepath],
    stdout=outfile,
    stderr=subprocess.PIPE,
  )
  _, err = proc.communicate()
  outfile.close()

  if err:
    with open(os.path.join(OUTPUT_LOGS, '%s.err' % img_name), 'w') as f:
      f.write(err)

  # save results into database
  return err


def render_batch(n_renders, idx_start=0):
  print "Starting renders %d through %d" % (idx_start, idx_start+n_renders-1)
  pool = multiprocessing.Pool(multiprocessing.cpu_count())
  args = []
  for idx in range(idx_start, idx_start+n_renders):
    foreground = Image.generate_foreground()
    background = Image.generate_background()
    args.append(([foreground, background], '%d_a' % idx))
    args.append(([background], '%d_b' % idx))
    args.append(([foreground], '%d_c' % idx))
  errors = pool.map(render, args)

  if any(errors):
    for idx, err in enumerate(errors):
      if err:
        print "Task %d threw an error; you may want to examine the logs" % (idx + idx_start)
        # Errors aren't always fatal and sometimes lead to working renders
  else:
    print "Renders %d through %d succeeded" % (idx_start, idx_start+n_renders-1)


if __name__ == '__main__':
  idx_start = 0
  batch_size = 100

  while True:
    render_batch(batch_size, idx_start)
    idx_start += batch_size

    time.sleep(5)
