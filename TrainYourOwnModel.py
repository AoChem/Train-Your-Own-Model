# Copyright @Ao Chen
# Train Your Own Model main script

# GUI packages
from tkinter import *
from tkinter import simpledialog
from tkinter import messagebox
from tkinter import filedialog

# System pakages
import os
import time
import numpy as np
import csv
from picamera import PiCamera
from time import gmtime, strftime

# Google Cloud Platform packages
from google.cloud import storage
from google.cloud import automl
from google.cloud.storage import Blob

# Media processing packages
import imutils
import cv2
from edgetpu.classification.engine import ClassificationEngine
from imutils.video import VideoStream
from PIL import Image

def initialization():
	global NameOfSts
	global NumOfSts
	NameOfSts = []
	NumOfSts = simpledialog.askinteger("Initializing", 
		"Input the number of states",
		parent=p,minvalue=1, maxvalue=3)

	for i in range(NumOfSts):
		NameOfSts.append(simpledialog.askstring("Initializing", 
			"State Name:", parent=p))

def picture_taking():
	camera = PiCamera()
	camera.resolution = (800, 480)
	camera.start_preview(fullscreen=False, window=(100, 200, 800, 480))

	taking_pictures=True

	def finish():
		camera.stop_preview()
		camera.close()
		pt.destroy()
	# 1st StatusPi
	def take_picture_1():
		print(NameOfSts[0]+" Picture Taken!")
		output = output_directory+'/'+strftime(NameOfSts[0]+"/image-%d-%m-%H:%M:%S.png", gmtime())
		camera.capture(output)
	# 2nd Status
	def take_picture_2():
		print(NameOfSts[1]+" Picture Taken!")
		output = output_directory+'/'+strftime(NameOfSts[1]+"/image-%d-%m-%H:%M:%S.png", gmtime())
		camera.capture(output)
	# 3rd Status
	def take_picture_3():
		print(NameOfSts[2]+" Picture Taken!")
		output = output_directory+'/'+strftime(NameOfSts[2]+"/image-%d-%m-%H:%M:%S.png", gmtime())
		camera.capture(output)

	pt = Toplevel()
	pt.title('Picture Taking')

	output_directory = filedialog.askdirectory(parent=pt,
		initialdir=os.getcwd(),
		title = "Please select the destination folder:")

	if output_directory == "":
		messagebox.showwarning("Warning", "Empty Path!")
		time.sleep(1)
		output_directory = filedialog.askdirectory()

	for x in range(NumOfSts):
		if not os.path.exists(output_directory+'/'+NameOfSts[x]+'/'):
			os.makedirs(output_directory+'/'+NameOfSts[x]+'/')

	if NumOfSts >= 1:
		sts1_button = Button(pt, text=NameOfSts[0], width=25, command=take_picture_1).pack()
		if NumOfSts >= 2:
			sts2_button = Button(pt, text=NameOfSts[1], width=25, command=take_picture_2).pack()
			if NumOfSts == 3:
				sts3_button = Button(pt, text=NameOfSts[2], width=25, command=take_picture_3).pack()

	finish_button = Button(pt, text='Finish', width=25, command=finish).pack()

	pt.mainloop()

def data_augmentation():
	import Augmentor

	def data_augmenting():
		NumOfAugSts = simpledialog.askinteger(
			"Data Augmenting",
			"Input the number of labels you want to augment:",
			parent=da,
			minvalue=1,
			maxvalue=3
			)
		sts = ['1st', '2nd', '3rd']

		for x in range(NumOfAugSts):
			print("Augmenting the "+sts[x]+" status...\n")
			NumOfSmp = simpledialog.askinteger("Data Augmenting",
				"Input the number of samples:",
				parent=da, minvalue=10, maxvalue=500)
			
			SrcPath = filedialog.askdirectory(parent=da,
				initialdir=os.getcwd(),
				title = "Please select the source folder:")
			if SrcPath == "":
				messagebox.showwarning("Warning", "Empty Path!")
				time.sleep(1)
				SrcPath = filedialog.askdirectory()
			else:
				SrcPath.replace('/', '\\')

			DstPath = filedialog.askdirectory(parent=da,
				initialdir=os.getcwd(),
				title = "Please select the destination folder:")
			if SrcPath == "":
				messagebox.showwarning("Warning", "Empty Path!")
				time.sleep(1)
				SrcPath = filedialog.askdirectory()
			else:
				SrcPath.replace('/', '\\')

			pl = Augmentor.Pipeline(source_directory=SrcPath,\
				output_directory=DstPath)

			if var1.get() == 1:
				pl.rotate(probability=0.8,
					max_left_rotation=10,
					max_right_rotation=10)
			if var2.get() == 1:
				pl.skew(probability=0.8,
					magnitude=0.2)
			if var3.get() == 1:
				pl.zoom(probability=0.8,
					min_factor=1.1,
					max_factor=1.5)
			if var4.get() == 1:
				pl.random_brightness(probability=0.8,
					min_factor=0.8,
					max_factor=1.2)
			
			pl.sample(NumOfSmp)

	da = Toplevel()
	da.title('Data Augmenting...')

	var1 = IntVar()
	Checkbutton(da, text='Rotation', variable=var1).pack()
	var2 = IntVar()
	Checkbutton(da, text='Skew & Tilt', variable=var2).pack()
	var3 = IntVar()
	Checkbutton(da, text='Zoom in', variable=var3).pack()
	var4 = IntVar()
	Checkbutton(da, text='Brightness', variable=var4).pack()

	Button(da, text='Augment Data', command=data_augmenting).pack()
	Button(da, text='Finish', command=da.destroy).pack()

	da.mainloop()

def model_training():
	def model_training_init(parent):
		mt = parent
		global display_name, model_name, model_filename, csv_name
		display_name = simpledialog.askstring("Initializing", 
			"Dataset Name:", parent=mt)
		model_name = simpledialog.askstring("Initializing", 
			"Model Name on Google Cloud Storage:", parent=mt)
		model_filename = simpledialog.askstring("Initializing", 
			"Model Name on Local Device:", parent=mt)
		csv_name = simpledialog.askstring("Initializing", 
			"*.csv File Name:", parent=mt)
		model_filename += '.tflite'
		csv_name += '.csv'

	def dataset_selecting(parent):
		mt = parent
		global image_path
		image_path = filedialog.askdirectory(parent=mt, initialdir=os.getcwd(),
			title="Please select the dataset you want to train:")

	def model_training_main(display_name, model_name, model_filename, csv_name):
		from ImageUploading import upload_image_excel # self_defined
		from dotenv import load_dotenv
		load_dotenv()

		# set up google cloud automl 
		project_id = os.getenv("PROJECT_ID")
		bucket_name = os.getenv("BUCKET_NAME")
		remote_model_filename = 'edgetpu_model.tflite' #tflite: TensorFlow Lite
		model_format = 'edgetpu_tflite'
		train_budget = 12000 # budget/1000 equals 1 node hour
		storage_client = storage.Client(project=project_id)
		client = automl.AutoMlClient()
		project_location = f"projects/{project_id}/locations/us-central1"
		bucket = storage_client.get_bucket(bucket_name)
		display_name=display_name
		model_name=model_name
		model_filename=model_filename
		csv_name=csv_name

		#----------------------Create an empty dataset----------------------

		print('Dataset Creation...')
		metadata = automl.ImageClassificationDatasetMetadata(
		    classification_type=automl.ClassificationType.MULTICLASS
		)
		dataset = automl.Dataset(
		    display_name=display_name,
		    image_classification_dataset_metadata=metadata
		)

		# Create a dataset with the dataset metadata in the region.
		response = client.create_dataset(parent=project_location,
			dataset=dataset)
		created_dataset = response.result()
		# Display the dataset information
		print("Dataset name: {}".format(created_dataset.name))
		print("Dataset id: {}".format(created_dataset.name.split("/")[-1]))
		dataset_id = created_dataset.name.split("/")[-1]

		#--------------Upload the images to google cloud bucket and 
		# create a *.csv file-------------
		print("Uploading Images...")
		status_list = NameOfSts
		upload_image_excel(bucket, bucket_name, display_name,
			image_path, status_list, csv_name)

		#----------------------Import the images to created dataset---------------------------------
		print("Importing Images...")
		# Read the *.csv file on Google Cloud
		remote_csv_path = 'gs://{0}/{1}'.format(bucket_name, csv_name)
		# Get the full path of the dataset.
		dataset_full_id = client.dataset_path(
			project_id, "us-central1", dataset_id
		)

		# Get the multiple Google Cloud Storage URIs
		# A Uniform Resource Identifier (URI) is a string of characters that unambiguously identifies a particular resource.
		input_uris = remote_csv_path.split(",")
		gcs_source = automl.GcsSource(input_uris=input_uris)
		input_config = automl.InputConfig(gcs_source=gcs_source)

		# Import data from the input URI
		response = client.import_data(name=dataset_full_id,
			input_config=input_config)

		print("Data imported. {}".format(response.result()))

		#-----------------Create and Train the Model-----------------------------------
		model_metadata = automl.ImageClassificationModelMetadata(
			train_budget_milli_node_hours=train_budget,
			model_type="mobile-high-accuracy-1"
		)
		model = automl.Model(
			display_name=model_name,
			dataset_id=dataset_id,
			image_classification_model_metadata = model_metadata,
		)

		# Create a model with the model metadata in the region.
		response = client.create_model(parent=project_location,
			model=model)

		print("Training operation name: {}".format(response.operation.name))
		print("Training started...")

		created_model = response.result()
		# Display the dataset information
		print("Model name: {}".format(created_model.name))
		print("Model id: {}".format(created_model.name.split("/")[-1]))

		#--------------------Listing Models--------------------------------
		request = automl.ListModelsRequest(parent=project_location,
			filter="")
		response = client.list_models(request=request)

		export_configuration = {
			'model_format': model_format,
			'gcs_destination':{'output_uri_prefix': 'gs://{}/'.format(bucket_name)}
		}

		for model in response:
			# check models in project and export new one
			if model.display_name == model_name:
				# export model to bucket
				model_full_id = client.model_path(project_id,
					"us-central1", model.name.split("/")[-1])
				response = client.export_model(name=model_full_id,
					output_config=export_configuration)

		# get information on model storage location and download it to local directory "models"
		export_metadata = response.metadata
		export_directory = export_metadata.export_model_details.output_info.gcs_output_directory

		model_dir_remote = export_directory + remote_model_filename
		model_dir_remote = "/".join(model_dir_remote.split("/")[-4:])
		model_dir = os.path.join("models", model_filename) 
		print(model_dir_remote)
		print(model_dir)

		def model_downloading():
			blob = Blob(model_dir_remote, bucket)

			with open(model_dir, "wb") as file_obj:
				blob.download_to_file(file_obj)

		model_downloading()
		# `download_to_file` function works from time to time

		print("Process completed, new model is now accessible locally.")

	# set up authentication credentials
	print("Initializing...")

	mt = Toplevel()
	mt.title("Model Training...")

	para_init_button = Button(mt, text='Initializing Parameters...', 
		command=lambda: model_training_init(mt)).pack()
	select_button = Button(mt, text='Select Dataset...', 
		command=lambda: dataset_selecting(mt)).pack()
	train_button = Button(mt, text='Train', 
		command=lambda: model_training_main(
			display_name, model_name, model_filename, csv_name)).pack()
	exit_button = Button(mt, text='Finish', 
		command=mt.destroy).pack()

	mt.mainloop()

def video_classification():

	print("[INFO] parsing class labels...")
	labels = {}

	label_txt = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select Label File:",
		filetypes=(("text files","*.txt"),("all files","*.*")))
	print(label_txt)
	# After training, the order of the states is arranged by GCP 
	# in a txt file stored in the same directory as the model
	# and no rule is found for the order

	# loop over the class labels file
	for row in open(label_txt):
		# unpack the row and update the labels dictionary
		(classID, label) = row.strip().split(" ", maxsplit=1)
		label = label.strip().split(",", maxsplit=1)[0]
		labels[int(classID)] = label

	model_tflite = filedialog.askopenfilename(initialdir=os.getcwd(),title="Select Model:",
		filetypes=(("tensor flow lite files:","*.tflite"),("all files","*.*")))

	print("[INFO] loading Coral model...")
	model = ClassificationEngine(model_tflite)

	# initialize the video stream and allow the camera sensor to warmup
	print("[INFO] starting video stream...")
	vs = VideoStream(src=0).start()
	# vs = VideoStream(usePiCamera=True).start()
	time.sleep(2.0)

	print('[INFO] press `q` to quit the classification mode')
	print('[INFO] press `t` to enter the training mode')
	training = False

	# loop over the frames from the video stream
	while True:
		# grab the frame from the threaded video stream and resize it
		# to have a maximum width of 500 pixels
		frame = vs.read()
		frame = imutils.resize(frame, width=500)
		orig = frame.copy()

		# prepare the frame for classification by converting (1) it from
		# BGR to RGB channel ordering and then (2) from a NumPy array to
		# PIL image format
		frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		frame = Image.fromarray(frame)

		# make predictions on the input frame
		start = time.time()
		results = model.classify_with_image(frame, top_k=1)
		end = time.time()

		color = (0, 0, 255)
		# ensure at least one result was found
		if len(results) > 0:
			# draw the predicted class label, probability, and inference
			# time on the output frame
			(classID, score) = results[0]
			text = "{}: {:.2f}% ({:.4f} sec)".format(labels[classID],
				score * 100, end - start)
			if score >= 0.7:
				if classID == 1:
					color = (0, 255, 0)
				elif classID == 2:
					color = (255, 0, 0)
				cv2.putText(orig, text, (10, 30), 
					cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

		# show the output frame and wait for a key press
		cv2.imshow("Frame", orig)
		key = cv2.waitKey(1) & 0xFF

		# if the `q` key was pressed, break from the loop
		if key == ord('q'):
			break

		# if the `t` key was pressed, change to the training mode
		if key == ord('t'):
			training = True
			break

	# do a bit of cleanup
	vs.stream.release()
	cv2.destroyAllWindows()
	vs.stop()

	while training:
		training = False
		print('Training Mode!')
		supp = Toplevel()
		Button(supp, text='Supplement Pictures', 
			command=picture_taking).pack()
		Button(supp, text='Train A New Model', 
			command=model_training).pack()
		Button(supp, text='Exit', 
			command=supp.destroy).pack()
		supp.mainloop()
		# disable the camera after classification or preview

def image_classification():
	def check_file_type(image):
		exts = {'.jpg', '.png'}
		file_valid = any(image.endswith(ext) for ext in exts) 
		return file_valid 

	output_csv_name = simpledialog.askstring("Image Classifying",
		"Output results' csv file name:", parent=p)
	output_csv_name += '.csv'

	path = filedialog.askdirectory(parent=p, initialdir=os.getcwd(),
		title="Please select testset:")
	files = os.listdir(path)
	print(files)

	print("[INFO] parsing class labels...")
	labels = {}

	label_txt = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select Label File:",
	filetypes=(("text files","*.txt"),("all files","*.*")))
	print(label_txt)

	for row in open(label_txt):
		# unpack the row and update the labels dictionary
		(classID, label) = row.strip().split(" ", maxsplit=1)
		label = label.strip().split(",", maxsplit=1)[0]
		labels[int(classID)] = label

	model_tflite = filedialog.askopenfilename(initialdir=os.getcwd(),title="Select Model:",
		filetypes=(("tensor flow lite files:","*.tflite"),("all files","*.*")))

	print("[INFO] loading Coral model...")
	model = ClassificationEngine(model_tflite)

	print("[INFO] making predictions...")

	# iterate the files in the image folder
	with open(output_csv_name, 'w') as f:
		writer = csv.writer(f)
		writer.writerow(['Index', 'Label', 'Score'])

		for file in files:
			if check_file_type(file) == False:
				# ignore this file and continue
				print('Invalid Extension')
				continue

			# file_dir -The filredir in local disk
			file_dir = os.path.join(path, file)

			# load the input image
			image = cv2.imread(file_dir)
			orig = image.copy()

			# prepare the image for classification by converting (1) it from BGR
			# to RGB channel ordering and then (2) from a NumPy array to PIL
			# image format
			image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
			image = Image.fromarray(image)

			# make predictions on the input image
			# start = time.time()
			results = model.classify_with_image(image, top_k=5)
			# end = time.time()
			# print("[INFO] classification took {:.4f} seconds...".format(
			# 	end - start))

			# loop over the results
			for (i, (classID, score)) in enumerate(results):
				# display the classification result to the terminal
				# print("{}. {}: {:.2f}%".format(i + 1, labels[classID],
				# 	score * 100))
				if i==0 and score>=0.7:
					writer.writerow([i, labels[classID], score*100])

		f.close()
	print('Finished!')

# create the parent window
p = Tk() # p: parent
p.title('Train Your Own Model')

init_button = Button(p, text='Initialization', 
	width=25, command=initialization).pack()

pt_button = Button(p, text='Take Pictures', 
	width=25, command=picture_taking).pack()

da_button = Button(p, text='Augment Data', 
	width=25, command=data_augmentation).pack()

mt_button = Button(p, text='Train Classification Model', 
	width=25, command=model_training).pack()

pm_button = Button(p, text='Classify Video', 
	width=25, command=video_classification).pack()

ts_button = Button(p, text='Classify Image', 
	width=25, command=image_classification).pack()

exit_button = Button(p, text='Exit', 
	width=25, command=p.destroy).pack()

p.mainloop()