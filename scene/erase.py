import os

from scipy import misc

from utils.core import WORKING_DIR

IMAGES_DIR = os.path.join(WORKING_DIR, 'renders', 'images')

def erase(idx):
  img_a_path = os.path.join(IMAGES_DIR, '%d_a.png' % idx)
  img_b_path = os.path.join(IMAGES_DIR, '%d_b.png' % idx)
  img_c_path = os.path.join(IMAGES_DIR, '%d_c.png' % idx)

  img_a = misc.imread(img_a_path)
  img_b = misc.imread(img_b_path)  # background
  img_c = misc.imread(img_c_path)  # foreground

  x, y, _ = img_c.shape  #
  assert(img_b.shape == (x, y, _))

  img_b[img_c[:,:,3]!=0] = 0

  misc.imsave(os.path.join(IMAGES_DIR, '%d_d.png' % idx), img_b)

if __name__ == '__main__':
  for idx in range(20):
    try:
      erase(idx)
    except:
      print "failed %d" % idx

