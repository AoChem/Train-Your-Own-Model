# This code is used to loop through each individual image in a given folder,
# and upload them to gcs one at a time.
# Also, a new pandas dataframe is created to store the location ,
# and their corresponding label of each image in gcs after being uploaded.
# The dataframe is finally converted to a *.csv file and uploaded to gcs.
# NOTE: it's essential to have a *.csv file 
# since it's the only way to do so programatically.


import os
import pandas as pd

# check whether the file is a valid image. For this app, only *.jpg and *.png extensions
# and return a boolean value
def check_file_type(image):
	exts = {'.jpg', '.png'}
	file_valid = any(image.endswith(ext) for ext in exts) 
	return file_valid 

def upload_image_excel(bucket, bucket_name, display_name, image_path, status_list, csv_name):
	# path to training image directory
	path = image_path
	idx = 0
	# create a new dataframe 
	# dataframe is Two-dimensional, size-mutable, potentially heterogeneous tabular data in pandas
	df = pd.DataFrame(columns = ['file', 'name'])

	# loop through the different type of labels in local disk
	for status in status_list:
		files = os.listdir(os.path.join(path, status))
		print(files)

		# iterate the files in the image folder
		for file in files:
			if check_file_type(file) == False:
				# ignore this file and continue
				print('Invalid Extension')
				continue

			# file_dir -The filredir in local disk
			file_dir = os.path.join(path, status, file)

			# remote_file_name - where we'd like to store the images in Google Cloud
			remote_file_name = os.path.join(display_name, status, file)

			# upload image to Google Cloud
			blob = bucket.blob(remote_file_name)
			# upload blob from named file in local disk
			blob.upload_from_filename(file_dir)

			# append the location of this image in Google Cloud to the excel sheet
			gs_name = 'gs://' + bucket_name + '/' + os.path.join(display_name, status, file)
			df.loc[idx] = [gs_name, status]
			idx = idx + 1

			print('Successfully uploaded: {0}', remote_file_name)

	# removed error code in story
	# convert the dataframe to a csv file
	df.to_csv(csv_name, header = False, index = False)
	# upload csv to google cloud
	blob = bucket.blob(csv_name)
	blob.upload_from_filename(csv_name)