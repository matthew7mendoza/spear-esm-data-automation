from pydantic import BaseModel, Field


DEFAULT_LLM_INSTRUCTIONS = (
    "You are a strict data management assistant. Your objective is to extract information "
    "from user-provided scientific documents and metadata to accurately answer form questions "
    "for Data Management Plans, ReadMes, and DOIs. "
    "Keep answers concise and strictly technical. If the provided document does not contain "
    "the answer to a requested question, DO NOT guess. Instead, add that exact question to the "
    "missing_information list."
)


class AnswerPair(BaseModel):
    question: str = Field(description="The exact form question.")
    answer: str = Field(description="The extracted answer.")

class FormResponses(BaseModel):
    extracted_answers: list[AnswerPair] = Field(
        description="List mapping the exact form question to the extracted answer."
    )

    missing_information: list[str] = Field(
        description="List of exact questions from the prompt that could not be answered using the text."
    )

#ENTER THE FORMAT OF THE DMP TEMPLATE HERE.
DOCUMENT_TEMPLATES = {
    "DMP": {
        "questions": [
            "1. General Description of Data",
            "1.1 Name of Data/Project:",
            "1.2 Project purpose & summary:",
            "1.3 Timeframe (One-time or ongoing):",
            "1.4 Temporal coverage:",
            "1.5 Geographic coverage:",
            "1.7 Type(s) of data:",
            "1.8 Approximate data volume:",
            "1.9 Data collection method(s):",
            "2 & 3. Contacts & Responsible Party",
            "Point of Contact (Name, Title, Affiliation, Email):",
            "Responsible Party (Name, Title, Email):",
            "4. Resources",
            "Have resources for management been identified?:",
            "5. Data Lineage and Quality",
            "5.1 Processing workflow:",
            "5.2 Quality control procedures:",
            "6. Data Documentation",
            "6.1 Does metadata comply with requirements?:",
            "6.3 URL of metadata folder or data catalog (DOI):",
            "7. Data Access",
            "7.2 Intended data access method(s):",
            "7.3 Name of facility providing access",
            "7.4 Tentative dissemination date:",
            "8. Data Preservation",
            "8.1 Long term data archive location:",
            "8.4 Data protection and backup plan:"
        ],
        "schema": FormResponses
    },
    "README": {
        "questions": [
            "GENERAL INFORMATION",
            "1. Title of Dataset:",
            "2. Creators/Author list Information (author list on paper? Different order?)",
            "2.A. Principal Investigator Contact Information (Name, Institution, Address, Email):",
            "2.B. Co-authors (Name, Institution, Address, Email):",
            "External user inquiries need to be directed to:",
            "3. Date of data collection (single date, range, approximate date):",
            "4. Geographic location of data collection:",
            "5. Information about funding sources that supported the collection of the data:",
            "SHARING/ACCESS INFORMATION",
            "1. Licenses/restrictions placed on the data:",
            "2. Links to publications that were used as references, or that cite or use the data:",
            "3. Links to other publicly accessible locations of the data:",
            "4. Links/relationships to ancillary data sets:",
            "5. Was data derived from another source?",
            "6. Recommended citation for this dataset:",
            "DATA & FILE OVERVIEW",
            "1. File List:",
            "2. Relationship between files, if important:",
            "3. Additional related data collected that was not included in the current data package:",
            "4. Are there multiple versions of the dataset?",
            "METHODOLOGICAL INFORMATION",
            "1. Description of methods used for collection/generation of data:",
            "2. Methods for processing the data:",
            "3. Instrument- or software-specific information needed to interpret the data:",
            "4. Standards and calibration information, if appropriate:",
            "5. Environmental/experimental conditions:",
            "6. Describe any quality-assurance procedures performed on the data:",
            "7. People involved with sample collection, processing, analysis and/or submission:",
            "DATA-SPECIFIC INFORMATION FOR: NetCDF files in tar.gz files",
            "NetCDF.1. Number of variables:",
            "NetCDF.2. Number of cases/rows:",
            "NetCDF.3. Variable List:",
            "NetCDF.4. Missing data codes:",
            "NetCDF.5. Specialized formats or other abbreviations used:",
            "DATA-SPECIFIC INFORMATION FOR: atmos_daily.static.nc",
            "atmos_daily.1. Number of variables:",
            "atmos_daily.2. Number of cases/rows:",
            "atmos_daily.3. Variable List:",
            "atmos_daily.4. Missing data codes:",
            "atmos_daily.5. Specialized formats or other abbreviations used:",
            "DATA-SPECIFIC INFORMATION FOR: land.static.nc",
            "land_static.1. Number of variables:",
            "land_static.2. Number of cases/rows:",
            "land_static.3. Variable List:",
            "land_static.4. Missing data codes:",
            "land_static.5. Specialized formats or other abbreviations used:"
        ],
        "schema": FormResponses
    }
}