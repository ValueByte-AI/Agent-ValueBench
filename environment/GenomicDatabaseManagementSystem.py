# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import html
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict



# Represents a single genomic sequence entry (a prostring) and relevant information about it.
class ProstringInfo(TypedDict):
    prostring_id: str
    sequence: str
    sequence_type: str
    description: str
    associated_gene_id: str
    associated_protein_id: str
    organism_id: str
    date_added: str

# Details about a gene, which may link to one or more prostrings.
class GeneInfo(TypedDict):
    gene_id: str
    name: str
    function: str
    organism_id: str

# Information about a protein that may be associated with a prostring.
class ProteinInfo(TypedDict):
    protein_id: str
    name: str
    function: str
    organism_id: str

# Organism or species information linked to prostrings, genes, or proteins.
class OrganismInfo(TypedDict):
    organism_id: str
    species_name: str
    taxonomy: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Prostrings: {prostring_id: ProstringInfo}
        self.prostrings: Dict[str, ProstringInfo] = {}
        # Genes: {gene_id: GeneInfo}
        self.genes: Dict[str, GeneInfo] = {}
        # Proteins: {protein_id: ProteinInfo}
        self.proteins: Dict[str, ProteinInfo] = {}
        # Organisms: {organism_id: OrganismInfo}
        self.organisms: Dict[str, OrganismInfo] = {}

        # Constraints:
        # - Each prostring must have a unique prostring_id.
        # - Genomic sequences must be stored in a standardized format (e.g., FASTA).
        # - Associations between prostrings, genes, proteins, and organisms should be consistently maintained.
        # - Only valid, non-duplicated entries are accepted for each entity type.

    @staticmethod
    def _normalize_sequence(sequence: str) -> str:
        if not isinstance(sequence, str):
            return sequence
        return html.unescape(sequence)

    def get_prostring_by_id(self, prostring_id: str) -> dict:
        """
        Retrieve the full details (sequence, metadata, associations) of a specific prostring by its prostring_id.

        Args:
            prostring_id (str): Unique identifier of the prostring to retrieve.

        Returns:
            dict:
                On success: {
                    "success": True,
                    "data": ProstringInfo
                }
                On failure: {
                    "success": False,
                    "error": "Prostring not found"
                }
        Constraints:
            - prostring_id must be present in the database.
        """
        if prostring_id not in self.prostrings:
            return {
                "success": False,
                "error": "Prostring not found"
            }
        return {
            "success": True,
            "data": self.prostrings[prostring_id]
        }

    def list_all_prostrings(self) -> dict:
        """
        Retrieve all prostring entries in the database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ProstringInfo]  # List of all prostring entries; may be empty if none exist
            }
        """
        all_prostrings = list(self.prostrings.values())
        return { "success": True, "data": all_prostrings }

    def get_gene_by_id(self, gene_id: str) -> dict:
        """
        Retrieve information about a specific gene by its gene_id.

        Args:
            gene_id (str): Unique identifier of the gene.

        Returns:
            dict:
                - On success:
                    { "success": True, "data": GeneInfo }
                - On failure:
                    { "success": False, "error": "Gene with gene_id '<id>' not found." }

        Constraints:
            - gene_id must exist in the database.
        """
        gene_info = self.genes.get(gene_id)
        if gene_info is None:
            return { "success": False, "error": f"Gene with gene_id '{gene_id}' not found." }
        return { "success": True, "data": gene_info }

    def get_protein_by_id(self, protein_id: str) -> dict:
        """
        Retrieve information about a specific protein by its unique protein_id.
    
        Args:
            protein_id (str): The identifier of the protein to retrieve.
    
        Returns:
            dict: 
                Success:
                    {
                        "success": True,
                        "data": ProteinInfo     # The protein's information dictionary.
                    }
                Failure:
                    {
                        "success": False,
                        "error": "Protein not found"
                    }
        Constraints:
            - The protein entry must exist for the given ID.
        """
        protein_info = self.proteins.get(protein_id)
        if protein_info is None:
            return { "success": False, "error": "Protein not found" }
        return { "success": True, "data": protein_info }

    def get_organism_by_id(self, organism_id: str) -> dict:
        """
        Retrieve organism/species information by organism_id.

        Args:
            organism_id (str): The unique identifier of the organism to retrieve.

        Returns:
            dict: {
                "success": True,
                "data": OrganismInfo  # organism details
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Organism not found"
            }

        Constraints:
            - Only organisms present in the database can be retrieved.
        """
        organism = self.organisms.get(organism_id)
        if organism is None:
            return { "success": False, "error": "Organism not found" }
        return { "success": True, "data": organism }

    def list_prostrings_by_gene(self, gene_id: str) -> dict:
        """
        List all prostrings associated with a particular gene_id.

        Args:
            gene_id (str): The gene_id whose associated prostrings are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[ProstringInfo],  # List of ProstringInfo dicts, may be empty if none found.
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, such as gene_id not found.
            }

        Constraints:
            - The provided gene_id must exist in the genes database.
            - Only valid, non-duplicated prostring entries are considered.
        """
        if gene_id not in self.genes:
            return {"success": False, "error": "Gene ID does not exist"}

        prostrings = [
            prostring_info for prostring_info in self.prostrings.values()
            if prostring_info["associated_gene_id"] == gene_id
        ]

        return {"success": True, "data": prostrings}

    def list_prostrings_by_protein(self, protein_id: str) -> dict:
        """
        List all prostrings associated with a particular protein_id.

        Args:
            protein_id (str): Protein identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[ProstringInfo]  # All prostrings where associated_protein_id == protein_id
            }
            or
            {
                "success": False,
                "error": str  # If protein_id does not exist
            }

        Constraints:
            - The protein_id must exist in the system.
            - Returns an empty list (with success=True) if no prostrings associated.
        """
        if protein_id not in self.proteins:
            return {"success": False, "error": "Protein does not exist"}

        result = [
            prostring for prostring in self.prostrings.values()
            if prostring["associated_protein_id"] == protein_id
        ]
        return {"success": True, "data": result}

    def list_prostrings_by_organism(self, organism_id: str) -> dict:
        """
        List all prostrings associated with a given organism_id.

        Args:
            organism_id (str): The organism's ID to search for associated prostrings.

        Returns:
            dict:
                - On success: {
                    "success": True,
                    "data": List[ProstringInfo]  # list may be empty if none found
                  }
                - On error: {
                    "success": False,
                    "error": str  # error message if organism_id doesn't exist
                  }

        Constraints:
            - organism_id must exist in the database (self.organisms)
            - Only prostrings whose 'organism_id' matches are returned
        """
        if organism_id not in self.organisms:
            return { "success": False, "error": "Organism does not exist." }

        result = [
            prostring for prostring in self.prostrings.values()
            if prostring["organism_id"] == organism_id
        ]
        return { "success": True, "data": result }

    def list_genes_by_organism(self, organism_id: str) -> dict:
        """
        List all genes associated with a particular organism_id.

        Args:
            organism_id (str): The unique identifier of the organism.

        Returns:
            dict
                success: True and data is a list of GeneInfo dicts (possibly empty if no genes found)
                success: False and error message if organism_id does not exist

        Constraints:
            - organism_id must exist in the database.
        """
        if organism_id not in self.organisms:
            return {"success": False, "error": "Organism not found"}

        gene_list = [
            gene_info for gene_info in self.genes.values()
            if gene_info["organism_id"] == organism_id
        ]

        return {"success": True, "data": gene_list}

    def list_proteins_by_organism(self, organism_id: str) -> dict:
        """
        List all protein entries (ProteinInfo) associated with the given organism_id.

        Args:
            organism_id (str): The identifier of the organism whose proteins are to be listed.

        Returns:
            dict:
                Success: {
                    "success": True,
                    "data": List[ProteinInfo]  # All proteins with the given organism_id (empty if none)
                }
                Failure: {
                    "success": False,
                    "error": str  # Reason for failure (e.g. organism not found)
                }

        Constraints:
            - Returned proteins will only be for valid organism IDs.
            - If organism_id does not exist in the system, returns an error.
        """
        if organism_id not in self.organisms:
            return { "success": False, "error": "Organism does not exist" }

        proteins = [
            protein_info for protein_info in self.proteins.values()
            if protein_info["organism_id"] == organism_id
        ]

        return { "success": True, "data": proteins }

    def get_associations_for_prostring(self, prostring_id: str) -> dict:
        """
        Retrieve associated gene, protein, and organism records for a specified prostring.

        Args:
            prostring_id (str): Unique identifier of the target prostring.

        Returns:
            dict: {
                "success": True,
                "data": {
                    "gene": GeneInfo or None,
                    "protein": ProteinInfo or None,
                    "organism": OrganismInfo or None
                }
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure, e.g. prostring does not exist
            }

        Constraints:
            - Returns None for associated records that cannot be found.
            - Only looks up associations present in the prostring record.
        """
        prostring = self.prostrings.get(prostring_id)
        if not prostring:
            return { "success": False, "error": "Prostring does not exist" }

        gene = self.genes.get(prostring["associated_gene_id"]) if prostring["associated_gene_id"] else None
        protein = self.proteins.get(prostring["associated_protein_id"]) if prostring["associated_protein_id"] else None
        organism = self.organisms.get(prostring["organism_id"]) if prostring["organism_id"] else None

        return {
            "success": True,
            "data": {
                "gene": gene,
                "protein": protein,
                "organism": organism
            }
        }

    def add_prostring(
        self,
        prostring_id: str,
        sequence: str,
        sequence_type: str,
        description: str,
        associated_gene_id: str,
        associated_protein_id: str,
        organism_id: str,
        date_added: str
    ) -> dict:
        """
        Add a new prostring entry to the genomic database.

        Args:
            prostring_id (str): Unique identifier for the prostring.
            sequence (str): Genomic sequence (must be FASTA formatted).
            sequence_type (str): Type of the sequence (e.g., DNA/RNA).
            description (str): Description of the prostring.
            associated_gene_id (str): Gene ID associated to the prostring (must exist).
            associated_protein_id (str): Protein ID associated to the prostring (must exist).
            organism_id (str): Organism ID related to the prostring (must exist).
            date_added (str): Date string when the entry is added.

        Returns:
            dict: {
                "success": True,
                "message": "Prostring added successfully"
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints:
            - prostring_id must be unique.
            - sequence must be in valid FASTA format.
            - associated_gene_id, associated_protein_id, organism_id must exist in the system.
        """
        sequence = self._normalize_sequence(sequence)

        # Check uniqueness
        if prostring_id in self.prostrings:
            return { "success": False, "error": "Duplicate prostring_id" }

        # Check valid FASTA format (very basic simulation: starts with '>' and at least one non-empty line after)
        if not sequence or not sequence.startswith(">") or len(sequence.splitlines()) < 2:
            return { "success": False, "error": "Sequence must be in FASTA format" }

        seq_lines = sequence.splitlines()
        if all(line.strip() == "" for line in seq_lines[1:]):
            return { "success": False, "error": "Sequence portion in FASTA is empty" }

        # Check valid associations
        if associated_gene_id and associated_gene_id not in self.genes:
            return { "success": False, "error": "Associated gene_id not found" }
        if associated_protein_id and associated_protein_id not in self.proteins:
            return { "success": False, "error": "Associated protein_id not found" }
        if organism_id not in self.organisms:
            return { "success": False, "error": "Associated organism_id not found" }

        # All constraints satisfied, create entry
        self.prostrings[prostring_id] = {
            "prostring_id": prostring_id,
            "sequence": sequence,
            "sequence_type": sequence_type,
            "description": description,
            "associated_gene_id": associated_gene_id,
            "associated_protein_id": associated_protein_id,
            "organism_id": organism_id,
            "date_added": date_added
        }

        return { "success": True, "message": "Prostring added successfully" }

    def update_prostring(
        self,
        prostring_id: str,
        updates: dict
    ) -> dict:
        """
        Update an existing prostring's fields, requiring re-validation of constraints.

        Args:
            prostring_id (str): The ID of the prostring to update.
            updates (dict): A dictionary of field-value pairs to update. Allowed keys:
                - sequence, sequence_type, description, associated_gene_id,
                  associated_protein_id, organism_id, date_added

        Returns:
            dict: {
                "success": True,
                "message": "Prostring updated successfully."
            }
            or
            {
                "success": False,
                "error": <error_message>
            }

        Constraints:
            - prostring_id must exist in the database.
            - Updated associations (associated_gene_id, associated_protein_id, organism_id) must reference valid existing entries.
            - The sequence (if updated) must be in FASTA format (basic check: begins with '>', etc.).
            - No uniqueness violation for prostring_id (not updatable).
        """
        # --- Existence check ---
        if prostring_id not in self.prostrings:
            return {"success": False, "error": "Prostring does not exist."}
        prostring = self.prostrings[prostring_id].copy()

        # --- Validate fields and associations ---
        # Sequence FASTA format basic check
        if "sequence" in updates:
            seq = self._normalize_sequence(updates["sequence"])
            updates = updates.copy()
            updates["sequence"] = seq
            seq_lines = seq.strip().splitlines()
            if len(seq_lines) < 2 or not seq_lines[0].startswith(">"):
                return {
                    "success": False,
                    "error": "Sequence must be in valid FASTA format (description line starts with '>')."
                }
            # Other checks (not comprehensive): can be extended as needed

        # Association checks
        if "associated_gene_id" in updates:
            gene_id = updates["associated_gene_id"]
            if gene_id and gene_id not in self.genes:
                return {"success": False, "error": f"Associated gene_id '{gene_id}' does not exist."}
        if "associated_protein_id" in updates:
            protein_id = updates["associated_protein_id"]
            if protein_id and protein_id not in self.proteins:
                return {"success": False, "error": f"Associated protein_id '{protein_id}' does not exist."}
        if "organism_id" in updates:
            organism_id = updates["organism_id"]
            if organism_id and organism_id not in self.organisms:
                return {"success": False, "error": f"Organism_id '{organism_id}' does not exist."}

        # --- Apply updates ---
        allowed_keys = [
            "sequence", "sequence_type", "description",
            "associated_gene_id", "associated_protein_id",
            "organism_id", "date_added"
        ]
        for key in updates:
            if key in allowed_keys:
                prostring[key] = updates[key]

        # Final constraint re-validation (associations and sequence are already checked)
        # No additional constraints necessary for update.

        # --- Commit ---
        self.prostrings[prostring_id] = prostring

        return {"success": True, "message": "Prostring updated successfully."}

    def delete_prostring(self, prostring_id: str) -> dict:
        """
        Remove a prostring entry by its unique prostring_id. After deletion,
        the prostring will no longer appear in the database. Any other entity's
        information is not updated, as associations are not actively tracked in
        genes, proteins, or organisms in this schema.

        Args:
            prostring_id (str): The unique ID of the prostring to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Prostring <prostring_id> deleted successfully."
            }
            OR
            {
                "success": False,
                "error": "Prostring with specified ID does not exist."
            }
        Constraints:
            - The prostring_id must exist.
            - Removes only the prostring and its direct references.
        """
        if prostring_id not in self.prostrings:
            return {
                "success": False,
                "error": "Prostring with specified ID does not exist."
            }
    
        del self.prostrings[prostring_id]
        return {
            "success": True,
            "message": f"Prostring {prostring_id} deleted successfully."
        }

    def add_gene(self, gene_id: str, name: str, function: str, organism_id: str) -> dict:
        """
        Add a new gene entry to the database, ensuring uniqueness and valid associations.

        Args:
            gene_id (str): Unique identifier for the gene.
            name (str): Gene name.
            function (str): Description of gene function.
            organism_id (str): The organism this gene belongs to (must exist in database).

        Returns:
            dict:
                - Success: { "success": True, "message": "Gene added successfully." }
                - Failure (duplicate gene_id): { "success": False, "error": "Gene ID already exists." }
                - Failure (invalid organism_id): { "success": False, "error": "Associated organism_id does not exist." }
                - Failure (missing fields): { "success": False, "error": "Missing required fields." }

        Constraints:
            - Gene ID must be unique/non-duplicate.
            - Associated organism_id must exist in database.
            - All fields must be present and non-empty.
        """
        # Check for missing fields or empty values
        if not all([gene_id, name, function, organism_id]):
            return { "success": False, "error": "Missing required fields." }
        # Check uniqueness
        if gene_id in self.genes:
            return { "success": False, "error": "Gene ID already exists." }
        # Validate organism association
        if organism_id not in self.organisms:
            return { "success": False, "error": "Associated organism_id does not exist." }

        # Build entry and add
        gene_info: GeneInfo = {
            "gene_id": gene_id,
            "name": name,
            "function": function,
            "organism_id": organism_id
        }
        self.genes[gene_id] = gene_info

        return { "success": True, "message": "Gene added successfully." }

    def update_gene(self, gene_id: str, update_fields: dict) -> dict:
        """
        Modify details of a gene, ensuring uniqueness and association consistency.

        Args:
            gene_id (str): The ID of the gene to update.
            update_fields (dict): Dictionary with fields to update. Supported fields are
                'name', 'function', and optionally 'organism_id'.

        Returns:
            dict: On success: { "success": True, "message": "Gene updated successfully." }
                  On error: { "success": False, "error": <reason> }

        Constraints:
            - Only valid, non-duplicated entries are accepted.
            - If gene_id is not found, update fails.
            - If updating organism_id, it must reference an existing organism.
            - If update_fields includes an unsupported key, update fails.
        """
        if gene_id not in self.genes:
            return {"success": False, "error": "Gene not found."}

        allowed_fields = {"name", "function", "organism_id"}
        invalid_fields = set(update_fields.keys()) - allowed_fields
        if invalid_fields:
            return {"success": False, "error": f"Invalid field(s) in update: {invalid_fields}"}

        curr_gene = self.genes[gene_id]

        # If organism_id is updated, ensure it exists
        if "organism_id" in update_fields:
            new_organism_id = update_fields["organism_id"]
            if new_organism_id not in self.organisms:
                return {"success": False, "error": "Associated organism does not exist."}

        # Apply updates
        for field, value in update_fields.items():
            curr_gene[field] = value

        return {"success": True, "message": "Gene updated successfully."}

    def delete_gene(self, gene_id: str) -> dict:
        """
        Remove a gene entry by its gene_id.
        All prostrings associated with this gene will be updated to dissociate (set associated_gene_id to empty string).
    
        Args:
            gene_id (str): Unique identifier for the gene to be deleted.

        Returns:
            dict:
                - On success:
                    {
                        "success": True,
                        "message": "Gene <gene_id> deleted. <N> prostrings dissociated."
                    }
                - On failure:
                    {
                        "success": False,
                        "error": "Gene not found."
                    }
    
        Constraints:
            - The given gene_id must exist.
            - All prostrings referencing the gene must be dissociated.
            - No removal/modification of other associated entities.
        """
        if gene_id not in self.genes:
            return { "success": False, "error": "Gene not found." }
    
        dissociated_count = 0
        for prostring in self.prostrings.values():
            if prostring.get("associated_gene_id") == gene_id:
                prostring["associated_gene_id"] = ""
                dissociated_count += 1
            
        del self.genes[gene_id]
    
        message = f"Gene {gene_id} deleted. {dissociated_count} prostrings dissociated."
        return { "success": True, "message": message }

    def add_protein(
        self,
        protein_id: str,
        name: str,
        function: str,
        organism_id: str,
    ) -> dict:
        """
        Add a new protein entry to the genomic database.

        Args:
            protein_id (str): Unique identifier for the protein (must not already exist).
            name (str): Name of the protein.
            function (str): Function/description of the protein.
            organism_id (str): ID of the organism associated with this protein (must exist in organisms).

        Returns:
            dict: {
                "success": True,
                "message": "Protein <protein_id> successfully added."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - protein_id must be unique.
            - All fields must be provided and non-empty.
            - organism_id must exist in the system.
        """
        # Validate required fields
        if not (protein_id and name and function and organism_id):
            return { "success": False, "error": "All fields (protein_id, name, function, organism_id) are required." }

        # Check uniqueness of protein_id
        if protein_id in self.proteins:
            return { "success": False, "error": f"Protein ID '{protein_id}' already exists." }

        # Check existence of organism_id
        if organism_id not in self.organisms:
            return { "success": False, "error": f"Organism ID '{organism_id}' does not exist." }

        # Create and add the protein entry
        new_protein = {
            "protein_id": protein_id,
            "name": name,
            "function": function,
            "organism_id": organism_id
        }
        self.proteins[protein_id] = new_protein

        return {
            "success": True,
            "message": f"Protein {protein_id} successfully added."
        }

    def update_protein(
        self,
        protein_id: str,
        name: str = None,
        function: str = None,
        organism_id: str = None
    ) -> dict:
        """
        Update existing protein details.

        Args:
            protein_id (str): The unique identifier of the protein to update.
            name (str, optional): New name for the protein.
            function (str, optional): New function description for the protein.
            organism_id (str, optional): New organism_id to associate with the protein. Must exist.

        Returns:
            dict: 
              - On success: { "success": True, "message": "Protein updated successfully." }
              - On failure: { "success": False, "error": <reason> }

        Constraints:
            - protein_id must already exist.
            - If updating organism_id, the given ID must exist in self.organisms.
            - At least one update field must be set (name, function, organism_id).
        """
        # Check if protein exists
        if protein_id not in self.proteins:
            return { "success": False, "error": "Protein with the given ID does not exist." }

        # No update fields provided
        if name is None and function is None and organism_id is None:
            return { "success": False, "error": "No update fields provided." }

        protein = self.proteins[protein_id]
        updated = False

        if name is not None:
            protein['name'] = name
            updated = True
    
        if function is not None:
            protein['function'] = function
            updated = True

        if organism_id is not None:
            if organism_id not in self.organisms:
                return { "success": False, "error": "Associated organism_id does not exist." }
            protein['organism_id'] = organism_id
            updated = True

        if updated:
            self.proteins[protein_id] = protein
            return { "success": True, "message": "Protein updated successfully." }
        else:
            return { "success": False, "error": "No update fields provided." }

    def delete_protein(self, protein_id: str) -> dict:
        """
        Delete a protein entry, maintaining association consistency.

        Args:
            protein_id (str): The ID of the protein to delete.

        Returns:
            dict: 
                On success:
                    {
                        "success": True,
                        "message": "Protein deleted successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": str  # Reason for failure (not found, still associated)
                    }

        Constraints:
            - Protein cannot be deleted if any prostring references it in its associated_protein_id field.
            - Protein must exist.
            - Associations between prostrings, proteins, and other entities must be maintained consistently.
        """
        if protein_id not in self.proteins:
            return {"success": False, "error": "Protein not found."}
    
        # Check for associations in Prostrings
        for prostring in self.prostrings.values():
            if prostring.get("associated_protein_id") == protein_id:
                return {
                    "success": False,
                    "error": "Cannot delete: protein is still associated with a prostring."
                }
    
        del self.proteins[protein_id]
        return {"success": True, "message": "Protein deleted successfully."}

    def add_organism(self, organism_id: str, species_name: str, taxonomy: str) -> dict:
        """
        Add a new organism to the database.

        Args:
            organism_id (str): Unique identifier for the organism.
            species_name (str): The scientific/species name of the organism.
            taxonomy (str): Taxonomic classification of the organism.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Organism added successfully."
                    }
                On failure (duplicate or validation error):
                    {
                        "success": False,
                        "error": "Explanation of the error."
                    }

        Constraints:
            - organism_id must be unique (not already present).
            - All fields must be non-empty strings.
        """
        # Basic input validation
        if not isinstance(organism_id, str) or not organism_id.strip():
            return { "success": False, "error": "organism_id must be a non-empty string." }
        if not isinstance(species_name, str) or not species_name.strip():
            return { "success": False, "error": "species_name must be a non-empty string." }
        if not isinstance(taxonomy, str) or not taxonomy.strip():
            return { "success": False, "error": "taxonomy must be a non-empty string." }

        if organism_id in self.organisms:
            return { "success": False, "error": "Organism with this ID already exists." }

        new_organism: OrganismInfo = {
            "organism_id": organism_id,
            "species_name": species_name,
            "taxonomy": taxonomy
        }
        self.organisms[organism_id] = new_organism

        return { "success": True, "message": "Organism added successfully." }

    def update_organism(
        self,
        organism_id: str,
        species_name: str = None,
        taxonomy: str = None,
    ) -> dict:
        """
        Update details of an organism entry.

        Args:
            organism_id (str): Unique identifier for the organism to update.
            species_name (str, optional): New species name to set.
            taxonomy (str, optional): New taxonomy string to set.

        Returns:
            dict:
                On success:
                    { "success": True, "message": "Organism updated successfully" }
                On failure:
                    { "success": False, "error": <error message> }

        Constraints:
            - Organism with the given organism_id must already exist.
            - At least one of 'species_name' or 'taxonomy' must be provided.
            - No new organisms can be added via this operation.
            - The organism_id itself cannot be changed.
        """
        if organism_id not in self.organisms:
            return {"success": False, "error": "Organism not found"}

        if species_name is None and taxonomy is None:
            return {"success": False, "error": "No update fields provided"}

        organism = self.organisms[organism_id]
        if species_name is not None:
            organism["species_name"] = species_name
        if taxonomy is not None:
            organism["taxonomy"] = taxonomy

        self.organisms[organism_id] = organism  # Not strictly necessary, but explicit

        return {"success": True, "message": "Organism updated successfully"}

    def delete_organism(self, organism_id: str) -> dict:
        """
        Remove an organism entry from the system. Before deletion, checks for dependent prostring, gene,
        and protein entities that reference this organism. If any dependencies exist, deletion is aborted
        and the list of blocking dependents is returned.

        Args:
            organism_id (str): The unique identifier of the organism to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Deleted organism <organism_id> successfully."
            }
            OR
            {
                "success": False,
                "error": "Organism not found." or "Cannot delete organism; dependent prostrings: [...], genes: [...], proteins: [...]"
            }

        Constraints:
            - Prevent deletion if any prostring, gene, or protein references this organism.
            - Associations must be consistently maintained.
        """

        if organism_id not in self.organisms:
            return {"success": False, "error": "Organism not found."}

        # Find dependents
        prostring_dependents = [p_id for p_id, p in self.prostrings.items() if p["organism_id"] == organism_id]
        gene_dependents = [g_id for g_id, g in self.genes.items() if g["organism_id"] == organism_id]
        protein_dependents = [pr_id for pr_id, pr in self.proteins.items() if pr["organism_id"] == organism_id]

        if prostring_dependents or gene_dependents or protein_dependents:
            details = (
                f"Cannot delete organism; dependent prostrings: {prostring_dependents}, "
                f"genes: {gene_dependents}, proteins: {protein_dependents}"
            )
            return {
                "success": False,
                "error": details
            }

        del self.organisms[organism_id]
        return {"success": True, "message": f"Deleted organism {organism_id} successfully."}

    def validate_prostring_entry(self, prostring: dict) -> dict:
        """
        Validate a proposed Prostring entry for:
            - New-entry uniqueness of prostring_id when creating a new record
            - FASTA format compliance for 'sequence'
            - Association integrity: associated_gene_id, associated_protein_id, organism_id must exist if provided/non-empty

        Args:
            prostring (dict): Proposed ProstringInfo fields as dictionary.

        Returns:
            dict: {
                "success": True,
                "message": str  # Validation success message
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure
            }

        Constraints/Notes:
            - prostring_id must be present.
            - If prostring_id does not already exist, it must be unique.
            - If prostring_id already exists, this tool validates the existing entry's formatting and associations instead of treating it as a duplicate-creation error.
            - sequence must be FASTA format (">" header, valid lines)
            - Any associated_gene_id, associated_protein_id, organism_id must refer to an existing object unless empty string/missing.
        """
        # Check prostring_id present
        prostring_id = prostring.get("prostring_id", "").strip()
        if not prostring_id:
            return {"success": False, "error": "Missing prostring_id."}

        existing_prostring = self.prostrings.get(prostring_id)
        validating_existing_entry = existing_prostring is not None

        # Basic FASTA format validation for "sequence"
        sequence = self._normalize_sequence(prostring.get("sequence", ""))
        sequence_lines = sequence.splitlines()
        if not sequence_lines:
            return {"success": False, "error": "Sequence is empty/not provided."}
        if not sequence_lines[0].startswith(">"):
            return {"success": False, "error": "Sequence is not in FASTA format (missing '>' header line)."}
        if len(sequence_lines) < 2:
            return {"success": False, "error": "Sequence is not in FASTA format (missing sequence lines after header)."}
        if all(line.strip() == "" for line in sequence_lines[1:]):
            return {"success": False, "error": "Sequence is not in FASTA format (empty sequence body)."}
        # Optional: check all non-header lines have only valid chars (restrict to basic nucleotides/amino acids if desired)
        allowed_chars = set("ACGTUNacgtun-")  # allow for nucleotides, gaps; consider more for proteins
        for line in sequence_lines[1:]:
            line = line.strip()
            if not line:
                continue
            # If very minimal, accept any uppercase/lowercase letters and '-'
            if not all((c.isalpha() or c == "-") for c in line):
                return {"success": False, "error": "Invalid characters detected in sequence line: '{}'.".format(line)}
    
        # Association checks
        gene_id = prostring.get("associated_gene_id", "")
        if gene_id and gene_id not in self.genes:
            return {"success": False, "error": f"Associated gene_id '{gene_id}' does not exist."}
        protein_id = prostring.get("associated_protein_id", "")
        if protein_id and protein_id not in self.proteins:
            return {"success": False, "error": f"Associated protein_id '{protein_id}' does not exist."}
        organism_id = prostring.get("organism_id", "")
        if not organism_id:
            return {"success": False, "error": "organism_id is required."}
        if organism_id not in self.organisms:
            return {"success": False, "error": f"Organism_id '{organism_id}' does not exist."}
    
        # If all checks passed
        if validating_existing_entry:
            return {"success": True, "message": f"Existing prostring entry '{prostring_id}' validated successfully."}
        return {"success": True, "message": f"Prostring entry '{prostring_id}' validated successfully."}

    def validate_gene_entry(self, gene_entry: dict) -> dict:
        """
        Validate gene data for uniqueness and correctness.

        Args:
            gene_entry (dict): Gene information. Required keys:
                - gene_id (str): Must be unique across existing genes.
                - name (str): Not empty.
                - function (str): Not empty.
                - organism_id (str): Must exist in organism database.

        Returns:
            dict:
                - If validation successful:
                    { "success": True, "message": "Gene entry is valid." }
                - If invalid:
                    { "success": False, "error": str }  # description of reason

        Constraints:
            - Each gene must have a unique gene_id.
            - All fields must be present and non-empty.
            - Associated organism_id must exist.
        """
        required_fields = ["gene_id", "name", "function", "organism_id"]
        for field in required_fields:
            if field not in gene_entry or not isinstance(gene_entry[field], str) or gene_entry[field].strip() == "":
                return { 
                    "success": False, 
                    "error": f"Missing or invalid field: {field}" 
                }
        gene_id = gene_entry["gene_id"]
        if gene_id in self.genes:
            return { 
                "success": False, 
                "error": f"Gene with gene_id '{gene_id}' already exists."
            }
        organism_id = gene_entry["organism_id"]
        if organism_id not in self.organisms:
            return { 
                "success": False, 
                "error": f"Organism ID '{organism_id}' does not exist."
            }
        return { "success": True, "message": "Gene entry is valid." }


class GenomicDatabaseManagementSystem(BaseEnv):
    def __init__(self, *, parameters=None):
        super().__init__()
        self.parameters = copy.deepcopy(parameters or {})
        self._mirrored_state_keys = set()
        self._inner = self._build_inner_env()
        self._apply_init_config(self._inner, self.parameters if isinstance(self.parameters, dict) else {})
        self._sync_from_inner()

    @staticmethod
    def _build_inner_env():
        try:
            return _GeneratedEnvImpl({})
        except Exception:
            return _GeneratedEnvImpl()

    @staticmethod
    def _apply_init_config(env, init_config):
        if not isinstance(init_config, dict):
            return
        for key, value in init_config.items():
            setattr(env, key, copy.deepcopy(value))

    def _sync_from_inner(self):
        reserved = {
            "parameters",
            "_inner",
            "_mirrored_state_keys",
            "tool_list",
            "env_description",
            "initial_parameter_schema",
            "default_initial_parameters",
            "tool_descs",
        }
        current = set()
        for key, value in vars(self._inner).items():
            if key.startswith("__") and key.endswith("__"):
                continue
            if key in reserved:
                continue
            setattr(self, key, copy.deepcopy(value))
            current.add(key)
        stale = getattr(self, "_mirrored_state_keys", set()) - current
        for key in stale:
            if hasattr(self, key):
                delattr(self, key)
        self._mirrored_state_keys = current

    def _call_inner_tool(self, tool_name: str, kwargs: Dict[str, Any]):
        func = getattr(self._inner, tool_name)
        result = func(**copy.deepcopy(kwargs or {}))
        self._sync_from_inner()
        return result

    def get_prostring_by_id(self, **kwargs):
        return self._call_inner_tool('get_prostring_by_id', kwargs)

    def list_all_prostrings(self, **kwargs):
        return self._call_inner_tool('list_all_prostrings', kwargs)

    def get_gene_by_id(self, **kwargs):
        return self._call_inner_tool('get_gene_by_id', kwargs)

    def get_protein_by_id(self, **kwargs):
        return self._call_inner_tool('get_protein_by_id', kwargs)

    def get_organism_by_id(self, **kwargs):
        return self._call_inner_tool('get_organism_by_id', kwargs)

    def list_prostrings_by_gene(self, **kwargs):
        return self._call_inner_tool('list_prostrings_by_gene', kwargs)

    def list_prostrings_by_protein(self, **kwargs):
        return self._call_inner_tool('list_prostrings_by_protein', kwargs)

    def list_prostrings_by_organism(self, **kwargs):
        return self._call_inner_tool('list_prostrings_by_organism', kwargs)

    def list_genes_by_organism(self, **kwargs):
        return self._call_inner_tool('list_genes_by_organism', kwargs)

    def list_proteins_by_organism(self, **kwargs):
        return self._call_inner_tool('list_proteins_by_organism', kwargs)

    def get_associations_for_prostring(self, **kwargs):
        return self._call_inner_tool('get_associations_for_prostring', kwargs)

    def add_prostring(self, **kwargs):
        return self._call_inner_tool('add_prostring', kwargs)

    def update_prostring(self, **kwargs):
        return self._call_inner_tool('update_prostring', kwargs)

    def delete_prostring(self, **kwargs):
        return self._call_inner_tool('delete_prostring', kwargs)

    def add_gene(self, **kwargs):
        return self._call_inner_tool('add_gene', kwargs)

    def update_gene(self, **kwargs):
        return self._call_inner_tool('update_gene', kwargs)

    def delete_gene(self, **kwargs):
        return self._call_inner_tool('delete_gene', kwargs)

    def add_protein(self, **kwargs):
        return self._call_inner_tool('add_protein', kwargs)

    def update_protein(self, **kwargs):
        return self._call_inner_tool('update_protein', kwargs)

    def delete_protein(self, **kwargs):
        return self._call_inner_tool('delete_protein', kwargs)

    def add_organism(self, **kwargs):
        return self._call_inner_tool('add_organism', kwargs)

    def update_organism(self, **kwargs):
        return self._call_inner_tool('update_organism', kwargs)

    def delete_organism(self, **kwargs):
        return self._call_inner_tool('delete_organism', kwargs)

    def validate_prostring_entry(self, **kwargs):
        return self._call_inner_tool('validate_prostring_entry', kwargs)

    def validate_gene_entry(self, **kwargs):
        return self._call_inner_tool('validate_gene_entry', kwargs)
