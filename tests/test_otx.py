import asyncio
import unittest
from unittest.mock import patch, MagicMock
from app.integrations.otx import OTXClient

class TestOTX(unittest.TestCase):
    @patch("app.integrations.otx.httpx.AsyncClient")
    def test_get_ip_reputation(self, mock_client_cls):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "pulse_info": {
                "count": 5,
                "pulses": [
                    {"tags": ["Malware", "C2"]},
                    {"tags": ["Scanner"]}
                ]
            }
        }
        
        mock_client = MagicMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = asyncio.Future()
        mock_client.get.return_value.set_result(mock_response)
        
        mock_client_cls.return_value = mock_client
        
        # Run test
        client = OTXClient(api_key="test_key")
        result = asyncio.run(client.get_ip_reputation("1.2.3.4"))
        
        print(f"Result: {result}")
        
        self.assertEqual(result["reputation"], 50) # 5 * 10
        self.assertIn("Malware", result["tags"])
        self.assertIn("Scanner", result["tags"])

if __name__ == "__main__":
    unittest.main()
