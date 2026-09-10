"""
MBA EDITORIAL DAILY - JSON MANAGER MODULE
Handles atomic file operations for storing editorial JSON files, updating index.json, and regenerating glossary.json.
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from config import DATA_DIR, INDEX_JSON_PATH, GLOSSARY_JSON_PATH
from logger import logger

class JSONManager:
    """
    Manages the repository-based JSON database.
    """

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def generate_slug(self, title: str) -> str:
        """Converts article title into clean URL-safe kebab-case slug."""
        slug = title.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug).strip("-")
        return slug[:60]

    def save_editorial(self, ai_data: Dict[str, Any], raw_date: str) -> bool:
        """
        Saves individual editorial JSON file into partitioned year/month directory, updates index.json, and regenerates glossary.json.
        """
        try:
            date_str = ai_data.get("date") or raw_date or datetime.utcnow().strftime("%Y-%m-%d")
            
            # Parse Date for Folder Structure YYYY/MM
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            year_str = dt.strftime("%Y")
            month_str = dt.strftime("%m")

            slug = ai_data.get("slug") or self.generate_slug(ai_data.get("title", "editorial"))
            editorial_id = f"{date_str}-editorial-01"

            # Auto-calculate dayNumber if missing
            if "dayNumber" not in ai_data or not ai_data["dayNumber"]:
                existing_count = 0
                if INDEX_JSON_PATH.exists():
                    try:
                        with open(INDEX_JSON_PATH, "r", encoding="utf-8") as f:
                            idx_data = json.load(f)
                            existing_count = idx_data.get("totalEditorials", 0)
                    except Exception:
                        pass
                ai_data["dayNumber"] = existing_count + 1

            # Enrich JSON metadata
            ai_data["id"] = editorial_id
            ai_data["slug"] = slug
            ai_data["date"] = date_str
            ai_data["generatedAt"] = datetime.utcnow().isoformat() + "Z"

            # Create Year and Month subdirectories
            month_dir = self.data_dir / year_str / month_str
            month_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{date_str}.json"
            file_path = month_dir / filename
            relative_file_path = f"{year_str}/{month_str}/{filename}"

            # 1. Write individual Editorial JSON file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(ai_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved editorial JSON file to {file_path}")

            # 2. Update index.json
            self._update_index(ai_data, relative_file_path)

            # 3. Regenerate glossary.json
            self._regenerate_glossary()

            return True

        except Exception as e:
            logger.error(f"Error saving editorial JSON: {e}")
            return False

    def _update_index(self, ai_data: Dict[str, Any], relative_file_path: str):
        """
        Updates root index.json with new entry, ensuring newest editorial is listed first.
        """
        index_data = {"lastUpdated": "", "totalEditorials": 0, "editorials": []}

        if INDEX_JSON_PATH.exists():
            try:
                with open(INDEX_JSON_PATH, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
            except Exception as e:
                logger.warning(f"Could not read index.json during update: {e}")

        existing_editorials: List[Dict[str, Any]] = index_data.get("editorials", [])

        # Check if entry already exists (upsert)
        new_entry = {
            "id": ai_data["id"],
            "slug": ai_data["slug"],
            "dayNumber": ai_data.get("dayNumber", 1),
            "date": ai_data["date"],
            "title": ai_data.get("mainTopic") or ai_data.get("title", ""),
            "filePath": relative_file_path,
            "tags": ai_data.get("tags", []),
            "difficulty": ai_data.get("difficulty", "Intermediate")
        }

        # Filter out existing entry with same slug or date to prevent duplication
        filtered = [item for item in existing_editorials if item.get("slug") != new_entry["slug"] and item.get("date") != new_entry["date"]]
        
        # Prepend newest entry first
        filtered.insert(0, new_entry)

        # Sort by date descending
        filtered.sort(key=lambda x: x.get("date", ""), reverse=True)

        index_data["lastUpdated"] = datetime.utcnow().isoformat() + "Z"
        index_data["totalEditorials"] = len(filtered)
        index_data["editorials"] = filtered

        with open(INDEX_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Updated index.json successfully. Total Editorials: {len(filtered)}")

    def _regenerate_glossary(self):
        """
        Scans all editorial JSON files in data directory and aggregates terminology dictionary.
        """
        terms_map: Dict[str, Dict[str, Any]] = {}

        for json_file in self.data_dir.rglob("*.json"):
            if json_file.name == "index.json":
                continue
            
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    ed = json.load(f)
                    
                ed_title = ed.get("mainTopic") or ed.get("title", "")
                ed_slug = ed.get("slug", "")
                ed_date = ed.get("date", "")
                
                # Check both terminologies and section5_keywords
                terminologies = ed.get("section5_keywords", []) or ed.get("terminologies", [])
                for t in terminologies:
                    term_name = (t.get("word") or t.get("term") or "").strip()
                    if not term_name:
                        continue
                    
                    simple_meaning = t.get("simpleMeaning") or t.get("simpleExplanation") or t.get("definition") or ""
                    key = term_name.lower()
                    if key not in terms_map:
                        terms_map[key] = {
                            "term": term_name,
                            "definition": t.get("definition") or simple_meaning,
                            "simpleExplanation": simple_meaning,
                            "editorials": []
                        }
                    
                    # Attach source editorial reference if not already attached
                    refs = terms_map[key]["editorials"]
                    if not any(r.get("slug") == ed_slug for r in refs):
                        refs.append({
                            "title": ed_title,
                            "slug": ed_slug,
                            "date": ed_date
                        })
            except Exception as e:
                logger.warning(f"Error parsing {json_file} for glossary regeneration: {e}")

        # Convert to sorted list
        sorted_terms = list(terms_map.values())
        sorted_terms.sort(key=lambda x: x["term"].lower())

        glossary_data = {
            "lastUpdated": datetime.utcnow().isoformat() + "Z",
            "terms": sorted_terms
        }

        with open(GLOSSARY_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(glossary_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Regenerated glossary.json successfully with {len(sorted_terms)} unique terms.")
