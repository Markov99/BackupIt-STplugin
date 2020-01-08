import os, sys
from datetime import datetime as dt
from collections import Counter
import sublime, sublime_plugin


class BackupIt(sublime_plugin.EventListener):

	def on_pre_save(self, view):
		"""Checking sublime settings""" 
		self.plugin_settings = sublime.load_settings('BackupIt.sublime-settings')
		self.max_backups = self.plugin_settings.get("max_backups")
		self.config_fileFullName = self.plugin_settings.get("config_file_name") 
		self.backups_folder_path = self.plugin_settings.get("backups_folder_path")

	def is_pathAbsoulute(self, path):
		return not path.split(":\\")[0] == path

	def is_backupIt_exists(self):
		'''Checking if "FileYouWantToBackup.backupIt.FileExtension" exists'''
		backupIt_file = self.fileName+".backupIt."+self.fileExt
		if os.path.exists(os.path.join(self.filePath, backupIt_file)) and os.path.isfile(os.path.join(self.filePath, backupIt_file)):
			os.remove(os.path.join(self.filePath, backupIt_file))
			return True
		else:
			return False	

	def on_new(self, view):
		"""Checking if the file has just been created"""
		self.is_new = True
		return self

	def is_backups_equal(self, view):
		"""Comparing the last created backup and the new file"""
		try:
			last = max(os.listdir(self.in_backups_folder))
		except ValueError:
			return False
		with open(os.path.join(self.in_backups_folder, last), "rb") as file:
			last_content = file.read()
		with open(view.file_name(), "rb") as file:
			new_content = file.read()
		return last_content == new_content

	def on_post_save(self, view):
		"""The main magic happens here"""

		"""Initializing paths and file names"""
		self.filePath = os.path.dirname(view.file_name())
		self.fileFullName = os.path.basename(view.file_name())

		try:
			self.fileName = ".".join(self.fileFullName.split(".")[:-1])
			self.fileExt = ".".join(self.fileFullName.split(".")[-1:])
		except ValueError:
			self.fileName = self.fileFullName
			self.fileExt = ""

		if not self.is_pathAbsoulute(self.backups_folder_path):	
			self.backups_folder_path = os.path.join(self.filePath, self.backups_folder_path)
		self.in_backups_folder = os.path.join(self.backups_folder_path, self.fileFullName)
		self.config_filePath = os.path.join(self.in_backups_folder, self.config_fileFullName)     


		"""Checking if the user wants to keep a backup"""
		try:
			self.is_new
		except AttributeError:
			self.is_new = False
		try:
			self.response
		except AttributeError:
			self.response = False

		if self.is_new and not os.path.exists(self.in_backups_folder):
			self.response = sublime.yes_no_cancel_dialog(
				'''Are you want to store backups for this file ?\n
				If you will decide to do it later: create
				a new file in format "YourFileName.backupIt.Extension"
				and put it in the same folder. Next time you
				save your file, it will start backing up''') 
			

		if os.path.exists(self.in_backups_folder) or self.is_backupIt_exists() or (self.is_new and self.response == sublime.DIALOG_YES):
			self.is_new = False 

			"""Creating directories for backups"""
			if not os.path.exists(self.backups_folder_path):
				os.makedirs(self.backups_folder_path)
			if not os.path.exists(self.in_backups_folder):
				os.makedirs(self.in_backups_folder)
				with open(self.config_filePath, "wb") as cfg:
					pass


			"""Creating a new backup"""
			if not self.is_backups_equal(view):
				try:
					backup = open("".join([self.in_backups_folder, "\\", self.fileName, " {}.", self.fileExt]).format(dt.now().strftime('%Y-%m-%d %Hh%Mm%Ss')), 'wb')
					file = open(view.file_name(), "rb")
					backup.write(file.read())
					file.close()
					backup.close()
				except Exception:
					raise Exception

			"""Checking local config"""
			if os.path.exists(self.config_filePath):
				try:
					with open(self.config_filePath, "rb") as cfg:
						local_cfg = int(cfg.read())
				except ValueError:
					local_cfg = None
				if not local_cfg == None:	
					self.max_backups = local_cfg



			"""Getting rid of old backups"""
			if len(os.listdir(self.in_backups_folder)) > self.max_backups:
				backup_files = []
				for backups in os.listdir(self.in_backups_folder):
					backup_files.append(backups)
				backup_files.sort(reverse=True)
				for i in backup_files[self.max_backups:]:
					backup_dir = os.path.join(self.in_backups_folder, i)
					if os.path.isfile(backup_dir) and not backup_dir == self.config_filePath:
						os.remove(backup_dir)