import hashlib

class Hash:
    @staticmethod
    def _normalize(key: str) -> str:
        if not isinstance(key, str):
            return key
        lowered = key.lower()
        pattern = r"[A-Za-z0-9]+"
        match = re.findall(pattern, lowered)
        if not match:
            return "."
        return "".join(match)

    @staticmethod
    def normalize_inputs(inputs: list[str]) -> list[str]:
        return [Hash._normalize(input) for input in inputs if input]

    @staticmethod
    def hash_inputs(normalized_inputs: list[str]) -> list[str]:
        return [
            hashlib.sha256(str(normalized).encode()).hexdigest()
            for normalized in normalized_inputs
        ]

    @staticmethod
    def derive_key(hashes: list[str]) -> str:
        if len(hashes) == 0 or len(hashes) > 6:
            raise ValueError(
                f"Number of hashes must be between 1 and 6. Received {len(hashes)}."
            )

        if len(hashes) == 1:
            return hashes[0][:32]
        else:
            arg_char_count = (32 // len(hashes)) + 1
            truncated_hashes = [hash[:arg_char_count] for hash in hashes]
            return "".join(truncated_hashes)[:32]

    @staticmethod
    def create_hash(*inputs: str) -> str:
        try:
            normalized_inputs = Hash.normalize_inputs(inputs)
            if not normalized_inputs:
                raise ValueError("At least one input is required")

            hashes = Hash.hash_inputs(normalized_inputs)
            return Hash.derive_key(hashes)
        except Exception as e:
            print(f"An error occurred: {e}")
