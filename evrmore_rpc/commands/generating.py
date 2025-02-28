from typing import Dict, List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field

def wrap_generating_commands(client):
    """Add typed generating commands to the client."""
    
    def generate(nblocks: int, maxtries: int = 1000000) -> List[str]:
        """Mine blocks immediately to an address in the wallet."""
        return client.execute_command("generate", nblocks, maxtries)
    
    def generatetoaddress(nblocks: int, address: str, maxtries: int = 1000000) -> List[str]:
        """Mine blocks immediately to a specified address."""
        return client.execute_command("generatetoaddress", nblocks, address, maxtries)
    
    def getgenerate() -> bool:
        """Return if the server is set to generate coins."""
        return client.execute_command("getgenerate")
    
    def setgenerate(generate: bool, genproclimit: Optional[int] = None) -> None:
        """Set whether the server should generate coins."""
        if genproclimit is not None:
            return client.execute_command("setgenerate", generate, genproclimit)
        return client.execute_command("setgenerate", generate)
    
    # Add methods to client
    client.generate = generate
    client.generatetoaddress = generatetoaddress
    client.getgenerate = getgenerate
    client.setgenerate = setgenerate
    
    return client 