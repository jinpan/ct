import os
import random
import subprocess
import zipfile
import re
import shutil


data = []
for filepath in os.listdir('ShapeNetCore.v1'):
	if not filepath.endswith('.zip'):
		continue
	
	synsetID = filepath[:filepath.index('.')]
	z = zipfile.ZipFile(os.path.join('ShapeNetCore.v1', filepath))
	for filepath2 in z.namelist():
		if not filepath2.endswith('model.obj'):
			continue

		image_id = filepath2.split('/')[1]

		data.append((synsetID, image_id))
	z.close()


class Image(object):
	def __init__(self, model, scale=None, pos=None, rot=None, tags=None):
		self.model = model
		self.filepath = os.path.join('/', 'tmp', model[0], model[1], 'model.obj')
		self.scale = scale or (1., 1., 1.)
		self.pos = pos or (0., 0., 0.)
		self.rot = rot or (0., 0., 0.)
		self.tags = tags or []

	@classmethod
	def generate_random(cls):
		# pick a filepath at random
		model = data[random.randint(0, len(data)-1)]

		# pick a scale at random
		scale_k = random.randint(1, 4)
		scale = (scale_k, scale_k, scale_k)

		# pick a position at random
		pos = (random.randint(-3, 3), random.randint(-3, 3), random.randint(-3, 3))

		# pick a rotation at random
		rot = (0, 0, 0)

		# return the image
		return cls(model, scale, pos, rot, [])

	def to_string(self):
		result = "Image(filepath='{filepath}', scale={scale}, pos={pos}, rot={rot})".format(
			filepath=self.filepath,
			scale=self.scale,
			pos=self.pos,
			rot=self.rot,
		)

		return result


def render(images, img_idx):
	# write the render python script
	output_filepath = os.path.join('renders', '%d.png' % (img_idx))
	with open('render_airplane.py') as f:
		script = f.read().format(
			images=",\n".join(image.to_string() for image in images),
			output_filepath=output_filepath,
		)
	render_script_filepath = os.path.join('render_scripts', "%d.py" % img_idx)
	with open(render_script_filepath, 'w') as f:
		f.write(script)

	# unzip the required files
	for image in images:
		z = zipfile.ZipFile('ShapeNetCore.v1/%s.zip' % image.model[0])
		for filepath in z.namelist():
			if image.model[1] in filepath:
				z.extract(filepath, os.path.join('/', 'tmp'))
		z.close()

	# launch blender
	subprocess.call(["blender", "-b", "-P", render_script_filepath])
	
	# delete the unzipped required files
	for image in images:
		try:
			shutil.rmtree(os.path.join('/', 'tmp', image.model[0]))
		except:
			pass

	# save results into database


def main(n_renders):
	for img_idx in range(n_renders):
		# pick a random number of objects
		n_objects = random.randint(1, 5)

		images = [Image.generate_random() for _ in range(n_objects)]

		render(images, img_idx)


if __name__ == '__main__':
	n_renders = 10
	main(n_renders)
