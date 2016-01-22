import os

import bpy

class Image(object):
	def __init__(self, filepath, scale=None, pos=None, rot=None):
		self.filepath = filepath
		self.scale = scale or (1., 1., 1.)
		self.pos = pos or (0., 0., 0.)
		self.rot = rot or (0., 0., 0.)

def render(images, output_filepath):
	bpy.data.objects["Cube"].select = True
	bpy.ops.object.delete()

	for image in images:
		bpy.ops.import_scene.obj(filepath=image.filepath)
		bpy.ops.transform.resize(value=image.scale)
		bpy.ops.transform.translate(value=image.pos)
		for idx, value in enumerate(image.rot):
			axis = [0, 0, 0]; axis[idx] = 1
			bpy.ops.transform.rotate(value=value, axis=tuple(axis))

	bpy.context.scene.render.filepath = output_filepath
	bpy.ops.render.render(write_still = True)


if __name__ == '__main__':
	images = [
{images}
	]

	render(images, "{output_filepath}")

