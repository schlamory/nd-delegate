import yaml, pyaml, os, glob

import transcribe

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

pending_tasks = [transcribe.TranscriptionTask.load(yml) for yml in
                                                        glob.glob(pending_dir + "/*.yml")]

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

for f in glob.glob(wormhole_dir + "/*.pdf"):
  ff = pending_dir + "/" + f.split("/")[-1]
  os.rename(f, ff)
  task = transcribe.TranscriptionTask.create(ff)
  task.submit()
  task.save(pending_dir + "/" + task.name + ".yml")