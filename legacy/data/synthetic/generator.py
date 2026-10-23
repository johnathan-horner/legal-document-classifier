"""
Synthetic legal document dataset generator.
Creates realistic legal documents across different categories with embedded clauses.
"""
import random
import json
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid
from datetime import datetime, timedelta
import re

from ..config import ModelConfig, DataConfig


@dataclass
class SyntheticDocument:
    """Represents a synthetic legal document."""
    id: str
    document_class: str
    title: str
    content: str
    clauses: List[str]
    jurisdiction: str
    risk_level: str
    metadata: Dict[str, Any]


class LegalDocumentGenerator:
    """Generates synthetic legal documents for training."""

    def __init__(self, config: DataConfig):
        self.config = config
        self.random = random.Random(42)  # Seed for reproducibility

        # Legal entity names
        self.entity_names = [
            "Acme Corporation", "Beta Industries", "Gamma LLC", "Delta Partners",
            "Epsilon Holdings", "Zeta Enterprises", "Theta Solutions", "Kappa Corp",
            "Lambda Group", "Mu Holdings", "Nu Technologies", "Xi Ventures",
            "Omicron Inc", "Pi Systems", "Rho Dynamics", "Sigma Corp",
            "Tau Industries", "Upsilon Ltd", "Phi Consulting", "Chi Networks"
        ]

        # Person names
        self.person_names = [
            "John Smith", "Jane Doe", "Michael Johnson", "Sarah Williams",
            "David Brown", "Lisa Davis", "Robert Miller", "Jennifer Wilson",
            "William Moore", "Elizabeth Taylor", "James Anderson", "Mary Thomas",
            "Christopher Jackson", "Patricia White", "Daniel Harris", "Barbara Martin",
            "Matthew Thompson", "Susan Garcia", "Anthony Martinez", "Helen Robinson"
        ]

        # Jurisdictions
        self.jurisdictions = [
            "Delaware", "New York", "California", "Texas", "Florida",
            "Illinois", "Nevada", "Massachusetts", "Virginia", "Washington"
        ]

        # Legal terms and phrases
        self.legal_terms = {
            "contract_terms": [
                "whereas", "hereby", "pursuant to", "notwithstanding",
                "shall", "may", "will", "agrees", "covenants", "warrants"
            ],
            "court_terms": [
                "plaintiff", "defendant", "court", "jurisdiction", "venue",
                "motion", "order", "judgment", "decree", "injunction"
            ],
            "regulatory_terms": [
                "compliance", "regulation", "statute", "code", "provision",
                "requirement", "filing", "disclosure", "reporting", "audit"
            ]
        }

        # Clause templates
        self.clause_templates = self._initialize_clause_templates()

    def _initialize_clause_templates(self) -> Dict[str, List[str]]:
        """Initialize templates for different clause types."""
        return {
            "indemnification": [
                "Each party shall indemnify and hold harmless the other party from and against any and all claims, damages, losses, costs, and expenses arising from or relating to any breach of this agreement.",
                "The Company agrees to indemnify, defend, and hold harmless the Service Provider from any claims arising out of the Company's use of the services.",
                "Contractor shall indemnify Client against all claims, damages, and expenses resulting from Contractor's negligent performance of the work."
            ],
            "liability_limitation": [
                "In no event shall either party be liable for any indirect, incidental, special, consequential, or punitive damages, regardless of the theory of liability.",
                "The total liability of Company under this agreement shall not exceed the amount paid by Customer in the twelve months preceding the claim.",
                "Provider's liability is limited to direct damages only and shall not exceed $100,000 in the aggregate."
            ],
            "termination": [
                "This agreement may be terminated by either party upon thirty (30) days written notice to the other party.",
                "Either party may terminate this agreement immediately upon written notice if the other party materially breaches any provision hereof.",
                "This agreement shall automatically terminate upon the occurrence of any bankruptcy or insolvency proceeding involving either party."
            ],
            "non_compete": [
                "Employee agrees not to engage in any business that competes with the Company for a period of two years following termination of employment.",
                "For a period of one year after the termination of this agreement, Contractor shall not solicit or provide services to any client of the Company.",
                "Executive shall not, directly or indirectly, compete with the business of the Company within the geographic area for eighteen months."
            ],
            "data_sharing": [
                "The parties acknowledge that confidential information may be shared and agree to maintain the confidentiality of such information.",
                "Each party agrees to implement appropriate technical and organizational measures to protect personal data shared under this agreement.",
                "Data shared between the parties shall be used solely for the purposes outlined in this agreement and shall not be disclosed to third parties."
            ],
            "penalty_provisions": [
                "In the event of a material breach, the breaching party shall pay liquidated damages of $10,000 per day until the breach is cured.",
                "Late payment shall incur a penalty of 1.5% per month on the outstanding amount.",
                "Failure to meet performance standards may result in penalties up to 10% of the contract value."
            ]
        }

    def generate_complaint(self) -> SyntheticDocument:
        """Generate a legal complaint document."""
        plaintiff = self.random.choice(self.person_names)
        defendant = self.random.choice(self.entity_names)
        jurisdiction = self.random.choice(self.jurisdictions)
        case_number = f"{self.random.randint(2020, 2024)}-CV-{self.random.randint(1000, 9999)}"

        title = f"{plaintiff} v. {defendant}"

        content_parts = [
            f"IN THE SUPERIOR COURT OF {jurisdiction.upper()}",
            f"CASE NO. {case_number}",
            "",
            f"{plaintiff.upper()},",
            "Plaintiff,",
            "",
            "v.",
            "",
            f"{defendant.upper()},",
            "Defendant.",
            "",
            "COMPLAINT FOR DAMAGES",
            "",
            "TO THE HONORABLE COURT:",
            "",
            f"Plaintiff {plaintiff} hereby complains against Defendant {defendant} as follows:",
            "",
            "1. JURISDICTION AND VENUE",
            f"This Court has jurisdiction over this matter pursuant to the laws of {jurisdiction}.",
            "Venue is proper in this jurisdiction because the events giving rise to this action occurred within this county.",
            "",
            "2. PARTIES",
            f"Plaintiff {plaintiff} is a resident of {jurisdiction}.",
            f"Defendant {defendant} is a corporation organized under the laws of {jurisdiction} with its principal place of business in {jurisdiction}.",
            "",
            "3. STATEMENT OF FACTS",
            f"On or about {self._random_date()}, Plaintiff entered into an agreement with Defendant.",
            "Defendant failed to perform its obligations under the agreement, causing damages to Plaintiff.",
            "Despite demand, Defendant has refused to cure its breach or compensate Plaintiff for damages.",
            "",
            "4. CAUSES OF ACTION",
            "",
            "COUNT I - BREACH OF CONTRACT",
            "Plaintiff incorporates by reference all preceding paragraphs.",
            "Defendant breached the agreement by failing to perform its material obligations.",
            "As a direct and proximate result of Defendant's breach, Plaintiff suffered damages in an amount to be proven at trial.",
            "",
            "COUNT II - NEGLIGENCE",
            "Defendant owed a duty of care to Plaintiff.",
            "Defendant breached that duty by acting negligently in its performance.",
            "Plaintiff suffered damages as a direct result of Defendant's negligence.",
            "",
            "PRAYER FOR RELIEF",
            "WHEREFORE, Plaintiff respectfully requests that this Court:",
            "A. Award compensatory damages in an amount to be proven at trial;",
            "B. Award punitive damages where permitted by law;",
            "C. Award costs and reasonable attorney's fees;",
            "D. Grant such other relief as this Court deems just and proper.",
            "",
            f"Dated: {datetime.now().strftime('%B %d, %Y')}",
            "",
            f"Respectfully submitted,",
            f"Attorney for Plaintiff"
        ]

        content = "\n".join(content_parts)

        # Add some high-risk clauses randomly
        clauses = []
        if self.random.random() < 0.3:
            clauses.extend(["penalty_provisions"])

        return SyntheticDocument(
            id=str(uuid.uuid4()),
            document_class="complaint",
            title=title,
            content=content,
            clauses=clauses,
            jurisdiction=jurisdiction,
            risk_level="medium" if clauses else "low",
            metadata={
                "case_number": case_number,
                "plaintiff": plaintiff,
                "defendant": defendant,
                "word_count": len(content.split())
            }
        )

    def generate_motion(self) -> SyntheticDocument:
        """Generate a court motion document."""
        moving_party = self.random.choice(["Plaintiff", "Defendant"])
        case_name = f"{self.random.choice(self.person_names)} v. {self.random.choice(self.entity_names)}"
        jurisdiction = self.random.choice(self.jurisdictions)
        motion_types = [
            "Motion to Dismiss", "Motion for Summary Judgment", "Motion to Compel Discovery",
            "Motion for Preliminary Injunction", "Motion to Strike", "Motion for Sanctions"
        ]
        motion_type = self.random.choice(motion_types)

        title = f"{moving_party}'s {motion_type}"

        content_parts = [
            f"IN THE SUPERIOR COURT OF {jurisdiction.upper()}",
            "",
            case_name.upper(),
            "",
            f"{moving_party.upper()}'S {motion_type.upper()}",
            "",
            f"TO THE HONORABLE COURT:",
            "",
            f"{moving_party} respectfully moves this Court for an order as follows:",
            "",
            "I. INTRODUCTION",
            f"This {motion_type.lower()} seeks relief based on the following grounds:",
            "",
            "II. STATEMENT OF FACTS",
            "The relevant facts are undisputed and establish the following:",
            f"1. The parties entered into litigation on {self._random_date()}.",
            "2. Discovery has proceeded in accordance with the court's scheduling order.",
            "3. The facts material to this motion are not in dispute.",
            "",
            "III. LEGAL STANDARD",
            f"The legal standard for a {motion_type.lower()} requires the moving party to demonstrate:",
            "1. A clear legal basis for the requested relief;",
            "2. That the motion is timely filed;",
            "3. That the requested relief is appropriate under the circumstances.",
            "",
            "IV. ARGUMENT",
            f"{moving_party} satisfies all requirements for the requested relief.",
            "The law clearly supports the position taken by the moving party.",
            "No genuine issue of material fact exists that would preclude granting this motion.",
            "",
            "V. CONCLUSION",
            f"For the foregoing reasons, {moving_party} respectfully requests that this Court grant this motion and provide such other relief as the Court deems just and proper.",
            "",
            f"Dated: {datetime.now().strftime('%B %d, %Y')}",
            "",
            f"Respectfully submitted,",
            f"Attorney for {moving_party}"
        ]

        content = "\n".join(content_parts)

        clauses = []
        # Motions typically don't have high-risk clauses

        return SyntheticDocument(
            id=str(uuid.uuid4()),
            document_class="motion",
            title=title,
            content=content,
            clauses=clauses,
            jurisdiction=jurisdiction,
            risk_level="low",
            metadata={
                "motion_type": motion_type,
                "moving_party": moving_party,
                "case_name": case_name,
                "word_count": len(content.split())
            }
        )

    def generate_contract(self) -> SyntheticDocument:
        """Generate a contract document."""
        party1 = self.random.choice(self.entity_names)
        party2 = self.random.choice(self.entity_names)
        while party2 == party1:
            party2 = self.random.choice(self.entity_names)

        jurisdiction = self.random.choice(self.jurisdictions)
        contract_types = [
            "Service Agreement", "Software License Agreement", "Employment Agreement",
            "Non-Disclosure Agreement", "Partnership Agreement", "Consulting Agreement"
        ]
        contract_type = self.random.choice(contract_types)

        title = f"{contract_type} between {party1} and {party2}"

        # Randomly select which clauses to include
        included_clauses = []
        clause_content = []

        for clause_type, templates in self.clause_templates.items():
            if self.random.random() < 0.4:  # 40% chance for each clause type
                included_clauses.append(clause_type)
                clause_content.append(self.random.choice(templates))

        content_parts = [
            f"{contract_type.upper()}",
            "",
            f"This {contract_type} (\"Agreement\") is entered into as of {self._random_date()} (\"Effective Date\") by and between {party1}, a corporation organized under the laws of {jurisdiction} (\"Company\"), and {party2}, a corporation organized under the laws of {jurisdiction} (\"Contractor\").",
            "",
            "RECITALS",
            "",
            "WHEREAS, Company desires to engage Contractor to provide certain services;",
            "WHEREAS, Contractor represents that it has the expertise and capability to perform such services;",
            "",
            "NOW, THEREFORE, in consideration of the mutual covenants contained herein, the parties agree as follows:",
            "",
            "1. SERVICES",
            "Contractor shall provide services as described in Exhibit A attached hereto and incorporated by reference.",
            "",
            "2. TERM",
            f"This Agreement shall commence on the Effective Date and continue for a period of {self.random.randint(1, 5)} years.",
            "",
            "3. COMPENSATION",
            f"Company shall pay Contractor ${self.random.randint(50, 500):,} per month for the services.",
            "",
            "4. OBLIGATIONS",
            "Each party shall perform its obligations hereunder in a professional and workmanlike manner."
        ]

        # Add clause content
        section_num = 5
        for i, clause in enumerate(clause_content):
            content_parts.extend([
                "",
                f"{section_num + i}. {included_clauses[i].replace('_', ' ').title()}",
                clause
            ])

        content_parts.extend([
            "",
            f"{section_num + len(clause_content)}. GOVERNING LAW",
            f"This Agreement shall be governed by the laws of {jurisdiction}.",
            "",
            f"{section_num + len(clause_content) + 1}. ENTIRE AGREEMENT",
            "This Agreement constitutes the entire agreement between the parties.",
            "",
            "IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.",
            "",
            f"{party1}",
            "",
            "By: _______________________",
            "Name:",
            "Title:",
            "",
            f"{party2}",
            "",
            "By: _______________________",
            "Name:",
            "Title:"
        ])

        content = "\n".join(content_parts)

        # Determine risk level based on clauses
        high_risk_clauses = ["penalty_provisions", "liability_limitation", "non_compete"]
        risk_level = "high" if any(clause in included_clauses for clause in high_risk_clauses) else "medium" if included_clauses else "low"

        return SyntheticDocument(
            id=str(uuid.uuid4()),
            document_class="contract",
            title=title,
            content=content,
            clauses=included_clauses,
            jurisdiction=jurisdiction,
            risk_level=risk_level,
            metadata={
                "contract_type": contract_type,
                "party1": party1,
                "party2": party2,
                "num_clauses": len(included_clauses),
                "word_count": len(content.split())
            }
        )

    def generate_regulatory_filing(self) -> SyntheticDocument:
        """Generate a regulatory filing document."""
        company = self.random.choice(self.entity_names)
        jurisdiction = self.random.choice(self.jurisdictions)
        filing_types = [
            "Annual Report (Form 10-K)", "Quarterly Report (Form 10-Q)",
            "Current Report (Form 8-K)", "Proxy Statement (DEF 14A)",
            "Registration Statement (Form S-1)"
        ]
        filing_type = self.random.choice(filing_types)

        title = f"{filing_type} - {company}"

        content_parts = [
            f"UNITED STATES",
            "SECURITIES AND EXCHANGE COMMISSION",
            "Washington, D.C. 20549",
            "",
            filing_type.upper(),
            "",
            "PURSUANT TO SECTION 13 OR 15(d) OF THE SECURITIES EXCHANGE ACT OF 1934",
            "",
            f"For the fiscal year ended December 31, {self.random.randint(2020, 2023)}",
            "",
            "Commission File Number: 001-12345",
            "",
            f"{company.upper()}",
            f"(Exact name of registrant as specified in its charter)",
            "",
            f"{jurisdiction}                                    12-3456789",
            "(State of incorporation)              (I.R.S. Employer Identification No.)",
            "",
            "Securities registered pursuant to Section 12(b) of the Act:",
            "",
            "PART I",
            "",
            "Item 1. Business",
            f"{company} is engaged in various business activities including technology solutions and consulting services.",
            "",
            "Item 1A. Risk Factors",
            "The following risk factors may materially affect our business:",
            "• Market competition may impact our revenue",
            "• Regulatory changes may affect our operations",
            "• Technology disruption may require significant investment",
            "",
            "Item 2. Properties",
            f"Our principal executive offices are located in {jurisdiction}.",
            "",
            "Item 3. Legal Proceedings",
            "We are subject to various legal proceedings and claims in the ordinary course of business.",
            "",
            "PART II",
            "",
            "Item 5. Market for Common Equity",
            "Our common stock is traded on NASDAQ under the symbol 'ABCD'.",
            "",
            "Item 7. Management's Discussion and Analysis",
            f"The following discussion should be read in conjunction with our financial statements.",
            "",
            "SIGNATURES",
            "",
            f"Pursuant to the requirements of Section 13 of the Securities Exchange Act of 1934, the registrant has duly caused this report to be signed on its behalf by the undersigned, thereunto duly authorized.",
            "",
            f"{company}",
            "",
            f"By: /s/ Chief Executive Officer",
            f"Date: {datetime.now().strftime('%B %d, %Y')}"
        ]

        content = "\n".join(content_parts)

        # Regulatory filings may have data sharing clauses
        clauses = []
        if self.random.random() < 0.2:
            clauses.append("data_sharing")

        return SyntheticDocument(
            id=str(uuid.uuid4()),
            document_class="regulatory_filing",
            title=title,
            content=content,
            clauses=clauses,
            jurisdiction=jurisdiction,
            risk_level="medium" if clauses else "low",
            metadata={
                "filing_type": filing_type,
                "company": company,
                "fiscal_year": self.random.randint(2020, 2023),
                "word_count": len(content.split())
            }
        )

    def generate_executive_order(self) -> SyntheticDocument:
        """Generate an executive order document."""
        jurisdiction = self.random.choice(self.jurisdictions)
        order_number = self.random.randint(2023001, 2024365)

        order_topics = [
            "Government Transparency and Accountability",
            "Environmental Protection Standards",
            "Public Health Emergency Preparedness",
            "Cybersecurity Infrastructure Protection",
            "Economic Development Initiatives"
        ]
        topic = self.random.choice(order_topics)

        title = f"Executive Order {order_number}: {topic}"

        content_parts = [
            f"EXECUTIVE ORDER {order_number}",
            "",
            f"{topic.upper()}",
            "",
            f"By the authority vested in me as Governor of the State of {jurisdiction}, and under the Constitution and laws of {jurisdiction}, it is hereby ordered:",
            "",
            "WHEREAS, the State has a compelling interest in promoting {topic.lower()};",
            "",
            f"WHEREAS, current practices require enhancement to better serve the citizens of {jurisdiction};",
            "",
            "WHEREAS, coordinated action among state agencies is necessary to achieve these objectives;",
            "",
            "NOW, THEREFORE, I hereby order the following:",
            "",
            "Section 1. Policy",
            f"It is the policy of the State of {jurisdiction} to ensure the highest standards in all relevant areas.",
            "",
            "Section 2. Definitions",
            "For purposes of this Order:",
            "a) 'State Agency' means any department, office, commission, authority, or other entity of state government;",
            "b) 'Implementation Plan' means the detailed plan required under Section 4;",
            "",
            "Section 3. Responsibilities",
            "Each State Agency shall:",
            "a) Review current policies and procedures;",
            "b) Identify areas for improvement;",
            "c) Implement necessary changes within 90 days;",
            "",
            "Section 4. Implementation",
            "The Secretary of State shall coordinate implementation of this Order and report progress quarterly.",
            "",
            "Section 5. Compliance",
            "All State Agencies shall comply with this Order and any implementing guidance issued pursuant to this Order.",
            "",
            "Section 6. Effective Date",
            f"This Order is effective immediately and shall remain in effect until superseded or revoked.",
            "",
            f"IN WITNESS WHEREOF, I have hereunto set my hand this {datetime.now().strftime('%d day of %B, %Y')}.",
            "",
            "______________________________",
            f"Governor of {jurisdiction}"
        ]

        content = "\n".join(content_parts)

        clauses = []
        # Executive orders typically don't have traditional contract clauses

        return SyntheticDocument(
            id=str(uuid.uuid4()),
            document_class="executive_order",
            title=title,
            content=content,
            clauses=clauses,
            jurisdiction=jurisdiction,
            risk_level="low",
            metadata={
                "order_number": order_number,
                "topic": topic,
                "word_count": len(content.split())
            }
        )

    def generate_legislative_text(self) -> SyntheticDocument:
        """Generate legislative text document."""
        jurisdiction = self.random.choice(self.jurisdictions)
        bill_number = f"H.R. {self.random.randint(1000, 9999)}"

        bill_topics = [
            "Consumer Privacy Protection",
            "Digital Infrastructure Investment",
            "Small Business Support",
            "Healthcare Accessibility",
            "Education Technology Advancement"
        ]
        topic = self.random.choice(bill_topics)

        title = f"{bill_number} - {topic} Act"

        content_parts = [
            f"{bill_number}",
            "",
            f"IN THE HOUSE OF REPRESENTATIVES",
            "",
            f"A BILL",
            "",
            f"To promote {topic.lower()}, and for other purposes.",
            "",
            f"Be it enacted by the Senate and House of Representatives of the United States of America in Congress assembled,",
            "",
            "SECTION 1. SHORT TITLE.",
            f"This Act may be cited as the '{topic} Act of {datetime.now().year}'.",
            "",
            "SECTION 2. FINDINGS.",
            "Congress finds the following:",
            f"(1) The importance of {topic.lower()} to the American people cannot be overstated;",
            "(2) Current law does not adequately address the challenges in this area;",
            "(3) Federal action is necessary to ensure comprehensive coverage;",
            "",
            "SECTION 3. DEFINITIONS.",
            "In this Act:",
            "(1) The term 'Secretary' means the Secretary of the relevant Cabinet department;",
            "(2) The term 'State' includes the District of Columbia and any territory or possession of the United States;",
            "",
            "SECTION 4. ESTABLISHMENT OF PROGRAM.",
            f"(a) IN GENERAL.—The Secretary shall establish a program to promote {topic.lower()}.",
            "(b) ADMINISTRATION.—The program shall be administered in accordance with regulations promulgated by the Secretary.",
            "",
            "SECTION 5. FUNDING.",
            "(a) AUTHORIZATION.—There are authorized to be appropriated such sums as may be necessary to carry out this Act.",
            f"(b) AVAILABILITY.—Amounts appropriated under subsection (a) shall remain available until expended.",
            "",
            "SECTION 6. REGULATIONS.",
            "Not later than 180 days after the date of enactment of this Act, the Secretary shall promulgate regulations to implement this Act.",
            "",
            "SECTION 7. EFFECTIVE DATE.",
            f"This Act shall take effect on the date that is 1 year after the date of enactment of this Act."
        ]

        content = "\n".join(content_parts)

        # Legislative text may have penalty provisions
        clauses = []
        if self.random.random() < 0.3:
            clauses.append("penalty_provisions")

        return SyntheticDocument(
            id=str(uuid.uuid4()),
            document_class="legislative_text",
            title=title,
            content=content,
            clauses=clauses,
            jurisdiction=jurisdiction,
            risk_level="medium" if clauses else "low",
            metadata={
                "bill_number": bill_number,
                "topic": topic,
                "word_count": len(content.split())
            }
        )

    def _random_date(self) -> str:
        """Generate a random date string."""
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2024, 12, 31)
        random_date = start_date + timedelta(
            days=self.random.randint(0, (end_date - start_date).days)
        )
        return random_date.strftime("%B %d, %Y")

    def generate_dataset(self, output_path: str) -> Dict[str, Any]:
        """
        Generate complete synthetic dataset.

        Args:
            output_path: Path to save the dataset

        Returns:
            Dataset statistics
        """
        documents = []
        class_counts = {cls: 0 for cls in ModelConfig().class_names}

        # Generate documents for each class
        generators = {
            "complaint": self.generate_complaint,
            "motion": self.generate_motion,
            "contract": self.generate_contract,
            "regulatory_filing": self.generate_regulatory_filing,
            "executive_order": self.generate_executive_order,
            "legislative_text": self.generate_legislative_text
        }

        for class_name, generator_func in generators.items():
            print(f"Generating {self.config.samples_per_class} {class_name} documents...")
            for _ in range(self.config.samples_per_class):
                doc = generator_func()
                documents.append(asdict(doc))
                class_counts[class_name] += 1

        # Shuffle documents
        self.random.shuffle(documents)

        # Save dataset
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        with open(output_path / "synthetic_legal_documents.json", "w") as f:
            json.dump(documents, f, indent=2)

        # Generate statistics
        stats = {
            "total_documents": len(documents),
            "class_distribution": class_counts,
            "clause_distribution": self._analyze_clauses(documents),
            "risk_distribution": self._analyze_risk_levels(documents),
            "jurisdiction_distribution": self._analyze_jurisdictions(documents),
            "average_word_count": sum(doc["metadata"]["word_count"] for doc in documents) / len(documents)
        }

        with open(output_path / "dataset_stats.json", "w") as f:
            json.dump(stats, f, indent=2)

        print(f"Generated {len(documents)} documents")
        print(f"Class distribution: {class_counts}")
        print(f"Saved to: {output_path}")

        return stats

    def _analyze_clauses(self, documents: List[Dict]) -> Dict[str, int]:
        """Analyze clause distribution in the dataset."""
        clause_counts = {clause: 0 for clause in ModelConfig().clause_classes}

        for doc in documents:
            for clause in doc["clauses"]:
                if clause in clause_counts:
                    clause_counts[clause] += 1

        return clause_counts

    def _analyze_risk_levels(self, documents: List[Dict]) -> Dict[str, int]:
        """Analyze risk level distribution."""
        risk_counts = {"low": 0, "medium": 0, "high": 0}

        for doc in documents:
            risk_level = doc["risk_level"]
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1

        return risk_counts

    def _analyze_jurisdictions(self, documents: List[Dict]) -> Dict[str, int]:
        """Analyze jurisdiction distribution."""
        jurisdiction_counts = {}

        for doc in documents:
            jurisdiction = doc["jurisdiction"]
            jurisdiction_counts[jurisdiction] = jurisdiction_counts.get(jurisdiction, 0) + 1

        return jurisdiction_counts


if __name__ == "__main__":
    config = DataConfig()
    generator = LegalDocumentGenerator(config)

    # Generate dataset
    stats = generator.generate_dataset("./output")
    print("Dataset generation completed!")
    print(f"Statistics: {json.dumps(stats, indent=2)}")