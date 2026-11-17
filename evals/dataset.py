"""Loads data from dataset to prompt"""

from pathlib import Path
import yaml


#__file__ is always location of dataset.py(current file)
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET= ROOT / "evals" / "datasets" / "support_triage.yaml"
DEFAULT_PROMPT_PATH = ROOT / "evals" / "prompts" / "triage_v1.txt"

class DatasetFileNotFound(Exception):
    "Runs when dataset yaml file is not found"

class LoadDataset():

    def __init__(self, dataset_path: Path | str = DEFAULT_DATASET, prompt_path: Path | str = DEFAULT_PROMPT_PATH) -> None:
        self.dataset_path = Path(dataset_path)
        self.prompt_path = Path(prompt_path)

    def load_cases(self) -> list[dict]:
        path = self.dataset_path
        if not path.exists():
            raise DatasetFileNotFound(f"dataset file not found: {path}. Create it by hand"
                                       f" or take help of the internet")
        with open(path,'r',encoding='utf-8') as c:
            case_data= list(yaml.safe_load(c)["cases"])
            return case_data

    def build_prompt(self, ticket_data: dict ) -> str:
        prompt_path = self.prompt_path

        #open closes 
        with open(prompt_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
        #replace {ticket} and append case data to prompt
        updated_prompt = file_content.replace('{ticket}', ticket_data["input"])
        return updated_prompt
        
         