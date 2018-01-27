import numpy as np
import cv2
import re
import os

class FrameExtractor(object):
	"""
	This is A Frame extractor.
	"""
	def __init__(self, video_path, label_file, total_frames, out_folder):
		super(FrameExtractor, self).__init__()
		self.video_path = video_path
		self.label_file = label_file
		self.total_frames = total_frames
		self.out_folder = out_folder
		self.video_names = list()
		self.num_snippets = list()

	def MakeExtractorPlan(self):
		with open(self.label_file, 'r') as f:
			records = f.readlines()
		self.num_videos = len(records)

		record_pattern = re.compile('(.*),(.*):(.*)')
		distribution = list()
		start_frame = list()
		end_frame = list()
		for record in records:
			video_name, annotations = record.strip().split(' ')
			self.video_names.append(video_name)

			annotations = annotations.split('\t')
			self.num_snippets.append(len(annotations))

			for i in xrange(len(annotations)):
				start_idx, end_idx, act_type = record_pattern.search(annotations[i]).groups()
				distribution.append(int(end_idx) - int(start_idx) + 1)
				start_frame.append(int(start_idx))
				print start_frame
				end_frame.append(int(end_idx))
				print end_frame

		distribution = np.asarray(distribution, dtype=int) # frame length of each snippet

		assignment = np.round(distribution.astype(float) / sum(distribution) * self.total_frames)
		print '{} frames will be extracted'.format(sum(assignment))

		assert(distribution >= assignment).all()

		strides = (distribution / assignment).astype(int)
		borders = ((distribution % assignment) / 2).astype(int) # central alignment
		print strides
		print borders

		plan = dict()
		cnt = 0
		for i in xrange(self.num_videos):
			video_name = self.video_names[i]
			for ii in xrange(self.num_snippets[i]):
				# (start, end, stride)
				plan['{}_{}'.format(video_name, ii)] = range(start_frame[cnt+ii]+borders[cnt+ii], end_frame[cnt+ii]-borders[cnt+ii], strides[cnt+ii])
			cnt += self.num_snippets[i]

		self.plan = plan
		

	def ExtractFrames(self):
		for i in xrange(self.num_videos):
			name = self.video_names[i]
			video_filename = os.path.join(self.video_path, '{}.MP4'.format(name))
			cap = cv2.VideoCapture(video_filename)
			if cap.isOpened():
				flag = True
			else:
				print 'Cannot open: {}'.format(video_filename)
				continue

			for j in xrange(self.num_snippets[i]):
				snippet_folder = os.path.join(self.out_folder, '{}_{}'.format(name, j))
				if not os.path.exists(snippet_folder):
					os.makedirs(snippet_folder)
				for idx in self.plan['{}_{}'.format(name, j)]:
					cap.set(1, idx)
					ret, frame = cap.read()
					if ret:
						out_filename = os.path.join(snippet_folder, '{}_{}_{}.jpg'.format(name, j, idx))
						cv2.imwrite(out_filename, frame)


	def run(self):
		self.MakeExtractorPlan()
		self.ExtractFrames()


if __name__ == '__main__':
	"""
	video_path: the root folder which holds all video files directly.(*.MP4)
	label_file: the path and the file name of the '*.txt' annotation file.
	total_frames: should be 79750 in total.
	out_folder: the output folder used to save the extracted frames.
	---------------------------------------------------------
	NOTICE! The CHINESE path might cause error sometimes.
	---------------------------------------------------------
	"""

	video_path = '/path/to/the/root/of/videos'
	label_file = '/path/to/the/annotation.txt'
	# the first label file
	label_file = '/home/wenxi/Desktop/labels/08-22-0622.txt'
	# the second label file
	# label_file = '/home/wenxi/Desktop/labels/08-22-0623.txt'
	total_frames = 1000
	out_folder = '/path/for/saving/frames'

	extractor = FrameExtractor(video_path, label_file, total_frames, out_folder)
	extractor.run()