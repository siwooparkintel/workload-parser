"""
Tests for PCIe-only SocWatch parser
"""

import pytest
from pathlib import Path
from workload_parser.parsers.socwatch_parser import PCIeParser


class TestPCIeParser:
    """Test cases for PCIe-only SocWatch data parsing."""
    
    @pytest.fixture
    def parser(self):
        """Create a PCIeParser instance."""
        return PCIeParser()
    
    def test_can_parse_pcie_only_file(self, parser, tmp_path):
        """Test detection of PCIe-only SocWatch files."""
        # Create test directory structure
        workload_dir = tmp_path / "UHX2_DC_006"
        workload_dir.mkdir()
        
        # Create required ETL files (without osSession)
        (workload_dir / "workload_extraSession.etl").touch()
        (workload_dir / "workload_hwSession.etl").touch()
        (workload_dir / "workload_infoSession.etl").touch()
        
        # Create CSV file
        csv_file = workload_dir / "workload.csv"
        csv_file.write_text("PCIe LPM Summary\n")
        
        # Should detect as PCIe-only file
        assert parser.can_parse(csv_file) is True
    
    def test_cannot_parse_full_socwatch(self, parser, tmp_path):
        """Test that full SocWatch files (with osSession) are not detected as PCIe-only."""
        # Create test directory structure
        workload_dir = tmp_path / "full_socwatch"
        workload_dir.mkdir()
        
        # Create ALL ETL files (including osSession)
        (workload_dir / "workload_extraSession.etl").touch()
        (workload_dir / "workload_hwSession.etl").touch()
        (workload_dir / "workload_infoSession.etl").touch()
        (workload_dir / "workload_osSession.etl").touch()  # This makes it full SocWatch
        
        # Create CSV file
        csv_file = workload_dir / "workload.csv"
        csv_file.write_text("Full SocWatch data\n")
        
        # Should NOT detect as PCIe-only file
        assert parser.can_parse(csv_file) is False
    
    def test_cannot_parse_incomplete_etl_set(self, parser, tmp_path):
        """Test that files with incomplete ETL sets are not detected."""
        # Create test directory structure
        workload_dir = tmp_path / "incomplete"
        workload_dir.mkdir()
        
        # Create only 2 ETL files (need 3)
        (workload_dir / "workload_extraSession.etl").touch()
        (workload_dir / "workload_hwSession.etl").touch()
        
        # Create CSV file
        csv_file = workload_dir / "workload.csv"
        csv_file.write_text("Incomplete data\n")
        
        # Should NOT detect as PCIe-only file
        assert parser.can_parse(csv_file) is False
    
    def test_parse_pcie_lpm_data(self, parser, tmp_path):
        """Test parsing of PCIe LPM residency data."""
        # Create test directory structure
        workload_dir = tmp_path / "UHX2_DC_006"
        workload_dir.mkdir()
        
        # Create required ETL files
        (workload_dir / "workload_extraSession.etl").touch()
        (workload_dir / "workload_hwSession.etl").touch()
        (workload_dir / "workload_infoSession.etl").touch()
        
        # Create CSV file with PCIe LPM data
        csv_content = """
PCIe LPM Summary - Sampled: Approximated Residency (Percentage)
Device,L0 (%),L0s (%),L1 (%),L2 (%)
NVM Express Controller,95.2,2.1,1.5,1.2

PCIe Link Active Summary - Sampled: Approximated Residency (Percentage)
Device,Active (%)
NVM Express Controller,12.5

PCIe LTR Snoop Summary - Sampled: Histogram
Device,<1us,1-10us,10-100us,>100us
NVM Express Controller,80.0,15.0,4.0,1.0
"""
        csv_file = workload_dir / "workload.csv"
        csv_file.write_text(csv_content)
        
        # Parse the file
        result = parser.parse(csv_file)
        
        # Verify result structure
        assert 'pcie_data' in result
        assert 'file_info' in result
        
        pcie_data = result['pcie_data']
        
        # Check PCIe LPM data
        assert 'L0 (%)_NVM        PCIe_LPM' in pcie_data
        assert pcie_data['L0 (%)_NVM        PCIe_LPM'] == '95.2'
        assert 'L0s (%)_NVM        PCIe_LPM' in pcie_data
        assert pcie_data['L0s (%)_NVM        PCIe_LPM'] == '2.1'
        
        # Check PCIe Active data
        assert 'Active (%)_NVM        PCIe_Active' in pcie_data
        assert pcie_data['Active (%)_NVM        PCIe_Active'] == '12.5'
        
        # Check PCIe LTR data
        assert '<1us_NVM        PCIe_LTRsnoop' in pcie_data
        assert pcie_data['<1us_NVM        PCIe_LTRsnoop'] == '80.0'
    
    def test_parse_empty_pcie_data(self, parser, tmp_path):
        """Test parsing of file with no PCIe data."""
        # Create test directory structure
        workload_dir = tmp_path / "empty"
        workload_dir.mkdir()
        
        # Create required ETL files
        (workload_dir / "workload_extraSession.etl").touch()
        (workload_dir / "workload_hwSession.etl").touch()
        (workload_dir / "workload_infoSession.etl").touch()
        
        # Create CSV file with no PCIe data
        csv_file = workload_dir / "workload.csv"
        csv_file.write_text("No PCIe data here\n")
        
        # Parse the file
        result = parser.parse(csv_file)
        
        # Should return empty pcie_data dict
        assert 'pcie_data' in result
        assert isinstance(result['pcie_data'], dict)
        assert len(result['pcie_data']) == 0
    
    def test_validate_data(self, parser):
        """Test data validation."""
        # Valid data
        valid_data = {
            'pcie_data': {'metric1': 'value1'},
            'file_info': {'path': '/some/path'}
        }
        assert parser.validate_data(valid_data) is True
        
        # Invalid data - missing pcie_data
        invalid_data = {
            'file_info': {'path': '/some/path'}
        }
        assert parser.validate_data(invalid_data) is False
        
        # Invalid data - wrong type
        invalid_data2 = {
            'pcie_data': "not a dict"
        }
        assert parser.validate_data(invalid_data2) is False
    
    def test_load_pcie_targets(self, parser):
        """Test loading PCIe targets from config."""
        targets = parser._load_pcie_targets()
        
        # Should load default targets
        assert len(targets) > 0
        
        # Check expected target structure
        for target in targets:
            assert 'key' in target
            assert 'devices' in target
            assert 'lookup' in target
        
        # Check for expected targets
        target_keys = [t['key'] for t in targets]
        assert 'PCIe_LPM' in target_keys
        assert 'PCIe_Active' in target_keys
        assert 'PCIe_LTRsnoop' in target_keys
    
    def test_multiple_devices(self, parser, tmp_path):
        """Test parsing data from multiple PCIe devices."""
        # Create test directory structure
        workload_dir = tmp_path / "multi_device"
        workload_dir.mkdir()
        
        # Create required ETL files
        (workload_dir / "workload_extraSession.etl").touch()
        (workload_dir / "workload_hwSession.etl").touch()
        (workload_dir / "workload_infoSession.etl").touch()
        
        # Create CSV file with multiple devices
        csv_content = """
PCIe LPM Summary - Sampled: Approximated Residency (Percentage)
Device,L0 (%),L0s (%),L1 (%),L2 (%)
NVM Express Controller,95.2,2.1,1.5,1.2
WiFi Adapter,80.0,10.0,8.0,2.0
Ethernet Controller,70.0,15.0,10.0,5.0
"""
        csv_file = workload_dir / "workload.csv"
        csv_file.write_text(csv_content)
        
        # Parse the file
        result = parser.parse(csv_file)
        pcie_data = result['pcie_data']
        
        # Should only extract NVM data (as per config)
        assert 'L0 (%)_NVM        PCIe_LPM' in pcie_data
        assert pcie_data['L0 (%)_NVM        PCIe_LPM'] == '95.2'
        
        # WiFi and Ethernet should not be extracted (not in device list)
        assert 'L0 (%)_WiFi        PCIe_LPM' not in pcie_data
        assert 'L0 (%)_Ethernet        PCIe_LPM' not in pcie_data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
