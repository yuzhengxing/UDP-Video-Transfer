from threading import Thread
from queue import Queue
import socket
import cv2
import numpy
import time
import sys
from config import Config

class FileVideoStream:
	
	def __init__(self, transform=None, queue_size=128):
		self.config =  Config()
		# initialize the file video stream along with the boolean
		# used to indicate if the thread should be stopped or not
		self.stream = cv2.VideoCapture(0)
		self.stream.set(cv2.CAP_PROP_MODE, cv2.CAP_MODE_YUYV)
		self.stopped = False
		self.transform = transform

		# initialize the queue used to store frames read from
		# the video file
		self.Q = Queue(maxsize=queue_size)
		# intialize thread
		self.thread = Thread(target=self.update, args=())
		self.thread.daemon = True

		self.address = None
		self.sock = None
		self.init_connection()

		self.frame_size = 0
		self.piece_size = 0
		self.frame_pieces = 0
		self.init_config()
		
		#压缩参数，后面cv2.imencode将会用到，对于jpeg来说，15代表图像质量，越高代表图像质量越好为 0-100，默认95
		encode_param=[int(cv2.IMWRITE_JPEG_QUALITY), 50]

	def init_config(self):
		# 初始化大小信息
		config = self.config
		
		w = int(config.get("camera", "w"))
		h = int(config.get("camera", "h"))
		d = int(config.get("camera", "d"))
		frame_pieces = int(config.get("camera", "pieces"))
		self.frame_size = w*h
		self.piece_size = w*h*d/frame_pieces

		# 初始化连接信息
		host = config.get("server", "host")
		port = config.get("server", "port")
		self.address = (host, int(port))

		# 初始化delay信息
		self.frame_delay = float(config.get("delay", "frame"))
		self.piece_delay = float(config.get("delay", "piece"))

	def init_connection(self):
		try:
			self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		except socket.error as msg:
			print(msg)
			sys.exit(1)
	
	def close_connection(self):
		self.sock.close()

	def start(self):
		# start a thread to read frames from the file video stream
		self.thread.start()
		return self

	def update(self):
		sock = self.sock
		address = self.address

		print("read1 camera")
		# keep looping infinitely
		while True:
			# if the thread indicator variable is set, stop the
			# thread
			print("hre")
			if self.stopped:
				break

			# otherwise, ensure the queue has room in it
			if not self.Q.full():
				print("read camera")
				# read the next frame from the stream
				try:
					(ret, frame) = self.stream.read()
				except:
					print("oh no")
					exit(404)

				if cv2.waitKey(1) & 0xFF == ord('q'):
					self.stopped = True
				
				# if there are transforms to be done, might as well
				# do them on producer thread before handing back to
				# consumer thread. ie. Usually the producer is so far
				# ahead of consumer that we have time to spare.
				#
				# Python is not parallel but the transform operations
				# are usually OpenCV native so release the GIL.
				#
				# Really just trying to avoid spinning up additional
				# native threads and overheads of additional
				# producer/consumer queues since this one was generally
				# idle grabbing frames.
				if self.transform:
					frame = self.transform(frame)

				# time.sleep(frame_delay)
				# add the frame to the queue
				frame_s = frame.flatten().tostring()

				time.sleep(self.frame_delay)
				for i in range(self.frame_pieces):
					time.sleep(self.piece_delay)
					print(self.piece_size)
					# frame_piece = s[i*46080:(i+1)*46080]+str.encode(str(i).zfill(2))
					# sock.sendto(frame_piece, address)
					# self.Q.put(frame)
			else:
				time.sleep(0.1)  # Rest for 10ms, we have a full queue
		
		self.stop()

	def slice_data(self, index, frame):
		pass

	def pack_data(self, data_len, index, create_time, data):
		"""
		Pack data over udp
		"""
		res = b''
		config = self.config

		name = config.get("header", "name")
		data_len_len = int(config.get("header", "data"))
		index_len = int(config.get("header", "index"))
		time_len = int(config.get("header", "time"))
		
		res += name.encode()
		res += data_len.to_bytes(data_len_len, byteorder="big")
		res += index.to_bytes(index_len, byteorder="big")
		res += create_time.to_bytes(time_len, byteorder="big")

		res += data

		return res

	def read(self):
		# return next frame in the queue
		return self.Q.get()

	def running(self):
		return self.more() or not self.stopped

	def more(self):
		# return True if there are still frames in the queue. If stream is not stopped, try to wait a moment
		tries = 0
		while self.Q.qsize() == 0 and not self.stopped and tries < 5:
			time.sleep(0.1)
			tries += 1

		return self.Q.qsize() > 0

	def stop(self):
		cv2.destroyAllWindows()
		self.stream.release()
		self.close_connection()
		# indicate that the thread should be stopped
		self.stopped = True
		# wait until stream resources are released (producer thread might be still grabbing frame)
		self.thread.join()

def SendVideo():
	# con = Config()
	# host = con.get("server", "host")
	# port = con.get("server", "port")
	
	# address = (host, int(port))
	
	# # address = ('10.18.96.207', 8002)
	# try:
	# 	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	# except socket.error as msg:
	# 	print(msg)
	# 	sys.exit(1)
		
	
	FileVideoStream().start()

	# capture = cv2.VideoCapture(0)
	# capture.set(cv2.CAP_PROP_MODE, cv2.CAP_MODE_YUYV)
	# #读取一帧图像，读取成功:ret=1 frame=读取到的一帧图像；读取失败:ret=0
	# ret, frame = capture.read()
	# encode_param=[int(cv2.IMWRITE_JPEG_QUALITY), 50]
	

	while False:
		#停止0.1S 防止发送过快服务的处理不过来，如果服务端的处理很多，那么应该加大这个值
		time.sleep(0.01)
		ret, frame = capture.read()

		# result, imgencode = cv2.imencode('.jpg', frame, encode_param)
		s = frame.flatten().tostring()

		# cur_time = time.time()
		# print(int(cur_time*1000))
		# continue
		
		for i in range(20):
			time.sleep(0.001)
			# print(i.to_bytes(1, byteorder='big'))
			sock.sendto(s[i*46080:(i+1)*46080]+i.to_bytes(1, byteorder='big'), address)

		# result, imgencode = cv2.imencode('.jpg', frame, encode_param)
		# data = numpy.array(imgencode)
		# stringData = data.tostring()
		
		# save data
		# cv2.imwrite('read video data.jpg', frame, encode_param)
		# show locally
		# cv2.imshow('read video data.jpg', frame)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
		
		# 读取服务器返回值
		# receive = sock.recvfrom(1024)
		# if len(receive): print(str(receive,encoding='utf-8'))
		# if cv2.waitKey(10) == 27: break
			
	# capture.release()
	# cv2.destroyAllWindows()
	# sock.close()

	
if __name__ == '__main__':
	SendVideo()
