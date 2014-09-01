import yaml, pyaml, os, glob

import transcribe
from transcribe import TranscriptionTask, TranscribePageAttempt

nd_dir = os.path.abspath(__file__ + "/../../../")
# nd_dir = "../../"

config = yaml.load(open(nd_dir + "/config/transcription_wormhole.yml"))
connection_config = yaml.load(open(nd_dir + "/config/aws_credentials.yml"))

connection_config["bucket_name"] = config["bucket_name"]
connection_config["sandbox"] = config["sandbox"]

transcribe.connect(**connection_config)


wormhole_dir = "/Users/amoryschlender/Desktop/wormhole"
pending_dir = wormhole_dir + "/pending"
finished_dir = wormhole_dir + "/archive"
results_dir = wormhole_dir + "/results"

pending_tasks = [TranscriptionTask.load(yml) for yml in glob.glob(pending_dir + "/*.yml")]

#Review existing tasks
for task in pending_tasks:
  task.review()
  print task.name, task.status
  if task.status == "FINISHED":
    for chart in task.get_charts():
      chart.write(results_dir)
    task.save(finished_dir + "/" + task.name + ".yml")
    os.remove(pending_dir + "/" + task.name + ".yml")
    os.rename(pending_dir + "/" + task.pdf_name, finished_dir + "/" + task.pdf_name)
  else:
    task.save(pending_dir + "/" + task.name + ".yml")

#Submit new tasks
for f in glob.glob(wormhole_dir + "/*.pdf"):
  ff = pending_dir + "/" + f.split("/")[-1]
  os.rename(f, ff)
  task = TranscriptionTask.create(ff)
  task.submit()
  task.save(pending_dir + "/" + task.name + ".yml")

#Handle redos
redo_file_path = wormhole_dir + "/redo.txt"
with open(redo_file_path) as f:
  redo_lines = f.readlines()

if len(redo_lines) >0:
  attempts_by_hit_id = {}
  for task in [TranscriptionTask.load(yml) for yml in glob.glob(finished_dir + "/*.yml")]:
    for page_task in task.children:
      for attempt in page_task.children:
        attempts_by_hit_id[attempt.hit.id] = attempt

  for hit_id in [line.split()[0] for line in redo_lines]:
    attempt = attempts_by_hit_id[hit_id]
    page_task = attempt.parent
    page_task.resubmit()
    task = page_task.parent
    task.save(pending_dir + "/" + task.name + ".yml")

  with open(wormhole_dir + "/redo.txt") as f:
    redo_lines = f.readlines()

  open(redo_file_path, 'w').close()





