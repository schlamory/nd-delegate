import yaml, pyaml, os, glob

import transcribe

nd_dir = os.path.abspath(__file__ + "/../../../")
# nd_dir = "../../"

connection_config = yaml.load(open(nd_dir + "/secret/aws_credentials.yaml"))
connection_config["bucket_name"] = "laura-charts"
connection_config["sandbox"] = False

transcribe.connect(**connection_config)

wormhole_dir = "/Users/amoryschlender/Desktop/wormhole"
pending_dir = wormhole_dir + "/pending"

pending_tasks = [transcribe.TranscriptionTask.load(yml) for yml in
                                                        glob.glob(pending_dir + "/*.yml")]

for task in pending_tasks:
  task.review()
  print task.name, task.status
  task.save(pending_dir + "/" + task.name + ".yml")
