"""Title value object with letter counting logic."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Title:
    """Immutable title value object."""

    value: str

    def letter_count(self) -> int:
        """
        Count letters in title (alphanumeric only, excludes spaces and punctuation).
        
        Returns:
            Number of alphanumeric characters in title.
        """
        if not self.value:
            return 0
        # Remove all non-alphanumeric characters
        alphanumeric_only = re.sub(r"[^a-zA-Z0-9]", "", self.value)
        return len(alphanumeric_only)

    def substring_by_letter_count(self, target_letter_count: int) -> "Title":
        """
        Extract substring with specified number of letters, preserving structure.
        
        This method extracts a substring from the beginning of the title that contains
        exactly target_letter_count alphanumeric characters, while preserving spaces
        and punctuation from the original structure.
        
        Examples:
            Title("Super Gay Title").substring_by_letter_count(3) -> "Sup"
            Title("Super Gay Title").substring_by_letter_count(9) -> "Super Gay"
            Title("Super-Gay!").substring_by_letter_count(5) -> "Super"
        
        Args:
            target_letter_count: Number of alphanumeric letters to include (must be >= 0)
            
        Returns:
            New Title with substring containing exactly target_letter_count letters.
            If target_letter_count is 0 or negative, returns empty Title.
            If target_letter_count exceeds total letters, returns full title.
        """
        if target_letter_count <= 0:
            return Title("")
        
        if not self.value:
            return Title("")
        
        # Count total letters in full title
        total_letters = self.letter_count()
        
        # If target exceeds total, return full title
        if target_letter_count >= total_letters:
            return self
        
        # Extract substring with exactly target_letter_count letters
        # Strategy: iterate through characters, count alphanumeric, preserve structure
        result_chars = []
        alpha_count = 0
        
        for char in self.value:
            if re.match(r"[a-zA-Z0-9]", char):
                if alpha_count < target_letter_count:
                    result_chars.append(char)
                    alpha_count += 1
                else:
                    # Reached target, stop adding alphanumeric chars
                    break
            else:
                # Keep non-alphanumeric only if we haven't reached target yet
                # This preserves spaces/punctuation within the extracted portion
                if alpha_count < target_letter_count:
                    result_chars.append(char)
        
        return Title("".join(result_chars))

    def add_letters(self, count: int) -> "Title":
        """
        Add letters to title.
        
        DEPRECATED: This method is kept for backward compatibility but should not be
        used with the new full_title strategy. Use substring_by_letter_count instead.
        
        Args:
            count: Number of letters to add (can be negative to remove)
            
        Returns:
            New Title with letters added/removed.
        """
        if count == 0:
            return self
        
        if count > 0:
            # Add letters (use 'X' as placeholder letter)
            new_value = self.value + "X" * count
        else:
            # Remove letters from end
            # Extract alphanumeric characters, count them, remove from end
            alphanumeric_only = re.sub(r"[^a-zA-Z0-9]", "", self.value)
            current_letters = len(alphanumeric_only)
            new_count = max(0, current_letters + count)  # count is negative
            
            if new_count == 0:
                new_value = ""
            else:
                # Rebuild: keep non-alphanumeric structure, truncate alphanumeric chars
                # Strategy: remove alphanumeric chars from end while preserving structure
                # Simple approach: count how many alphanumeric to keep, rebuild string
                chars_to_keep = new_count
                result_chars = []
                alpha_count = 0
                
                for char in self.value:
                    if re.match(r"[a-zA-Z0-9]", char):
                        if alpha_count < chars_to_keep:
                            result_chars.append(char)
                            alpha_count += 1
                    else:
                        # Keep non-alphanumeric if we haven't reached target
                        if alpha_count < chars_to_keep:
                            result_chars.append(char)
                
                new_value = "".join(result_chars)
        
        return Title(new_value)

    def __str__(self) -> str:
        """Return title value as string."""
        return self.value

    def __len__(self) -> int:
        """Return letter count."""
        return self.letter_count()
