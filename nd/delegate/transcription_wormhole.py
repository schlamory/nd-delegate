import yaml, pyaml, os, sys, glob, logging, datetime

import transcribe
from transcribe import TranscriptionTask, TranscribePageAttempt

def review_existing_tasks():
  pending_tasks = [TranscriptionTask.load(yml) for yml in glob.glob(pending_dir + "/*.yml")]
  for task in pending_tasks:
    logger.info("Reviewing task {0} ...".format(task.name))
    task.review()
    if task.status == "FINISHED":
      for chart in task.get_charts():
        logger.info("Writing chart: {0}/{1}".format(results_dir, chart.file_name))
        chart.write(results_dir)
      task.save(finished_dir + "/" + task.name + ".yml")
      os.remove(pending_dir + "/" + task.name + ".yml")
      pdf_path = pending_dir + "/" + task.pdf_name
      if os.path.exists(pdf_path):
        os.rename(pending_dir + "/" + task.pdf_name, finished_dir + "/" + task.pdf_name)
    else:
      task.save(pending_dir + "/" + task.name + ".yml")
    logger.info("Status: " + task.status)

def submit_new_tasks():
  for f in glob.glob(new_dir + "/*.pdf"):
    ff = pending_dir + "/" + f.split("/")[-1]
    os.rename(f, ff)
    task = TranscriptionTask.create(ff)
    logger.info("Submitting task {0} ...".format(task.name))
    task.submit(layout_id=config["layout_id"])
    task.save(pending_dir + "/" + task.name + ".yml")

def handle_redos():
  redo_file_path = config["redo_file"]
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
      task = page_task.parent
      logger.info("Resubmitting page {0} of task {1}".format(page_task.page_number, task.name))
      page_task.resubmit()
      task.save(pending_dir + "/" + task.name + ".yml")

    with open(redo_file_path) as f:
      redo_lines = f.readlines()

    open(redo_file_path, 'w').close()

if __name__ == "__main__":
  config_path = sys.argv[1]
  config = yaml.load(open(config_path))
  logging.basicConfig(filename=config["log_file"],level=logging.INFO)

  logger = logging.getLogger("transcription_wormhole")

  logger.info("Begin: " + datetime.datetime.today().__str__())

  connection_params = ["bucket_name", "aws_access_key_id", "aws_secret_access_key", "sandbox"]
  connection_config = dict([(k, config[k]) for k in connection_params])

  transcribe.connect(**connection_config)

  wormhole_dir = config["wormhole_dir"]
  new_dir = wormhole_dir + "/new"
  pending_dir = wormhole_dir + "/pending"
  finished_dir = wormhole_dir + "/archive"
  results_dir = wormhole_dir + "/results"

  review_existing_tasks()
  submit_new_tasks()
  handle_redos()

  logger.info("End: " + datetime.datetime.today().__str__())



