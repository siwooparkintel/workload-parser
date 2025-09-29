"""
Enhanced configuration system with DAQ, Socwatch, and PCIe target support.
Based on the old project's JSON configuration files but with better structure.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import json
import yaml
from pydantic import BaseModel, Field, validator

from .exceptions import ConfigurationError


class DAQTarget(BaseModel):
    """DAQ power rail target configuration."""
    name: str = Field(..., description="Power rail name (e.g., P_VCC_PCORE)")
    default_value: float = Field(-1, description="Default value if not found")
    unit: str = Field("W", description="Power unit (W, mW, etc.)")
    category: str = Field("power", description="Category (power, voltage, current)")
    
    class Config:
        extra = "allow"  # Allow additional fields for flexibility


class SocwatchTarget(BaseModel):
    """Socwatch target metric configuration."""
    key: str = Field(..., description="Target key/identifier")
    lookup: str = Field(..., description="Text to search for in Socwatch output")
    buckets: Optional[List[str]] = Field(None, description="Optional bucketing for P-state data")
    description: str = Field("", description="Human-readable description")
    
    class Config:
        extra = "allow"


class PCIeTarget(BaseModel):
    """PCIe target configuration."""
    key: str = Field(..., description="Target key/identifier")
    devices: List[str] = Field(default_factory=list, description="Device types to monitor (e.g., NVM)")
    lookup: str = Field(..., description="Text to search for in PCIe data")
    description: str = Field("", description="Human-readable description")
    
    class Config:
        extra = "allow"


class ParserSettings(BaseModel):
    """Individual parser configuration settings."""
    enabled: bool = Field(True, description="Whether parser is enabled")
    priority: int = Field(100, description="Parser priority (lower = higher priority)")
    options: Dict[str, Any] = Field(default_factory=dict, description="Parser-specific options")
    
    class Config:
        extra = "allow"


class OutputSettings(BaseModel):
    """Output configuration settings."""
    format: str = Field("excel", description="Output format (excel, json, csv)")
    filename_template: str = Field("{input_name}_allPower_v{version}.xlsx", description="Output filename template")
    include_raw_data: bool = Field(False, description="Include raw parsed data in output")
    excel_options: Dict[str, Any] = Field(default_factory=lambda: {
        "multiple_sheets": True,
        "summary_sheet": True,
        "formatting": True
    })
    
    class Config:
        extra = "allow"


class LoggingSettings(BaseModel):
    """Logging configuration settings."""
    level: str = Field("INFO", description="Logging level")
    format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    file_logging: bool = Field(False, description="Enable file logging")
    log_file: str = Field("workload_parser.log", description="Log file path")
    
    class Config:
        extra = "allow"


class EnhancedParserConfig(BaseModel):
    """Enhanced configuration model with support for all old project features."""
    
    # Basic settings
    version: str = Field("2.0.0", description="Configuration version")
    description: str = Field("Enhanced Workload Parser Configuration", description="Configuration description")
    
    # Target configurations (from old project)
    daq_targets: Dict[str, DAQTarget] = Field(default_factory=dict, description="DAQ power rail targets")
    socwatch_targets: List[SocwatchTarget] = Field(default_factory=list, description="Socwatch metric targets")
    pcie_targets: List[PCIeTarget] = Field(default_factory=list, description="PCIe metric targets")
    
    # Parser configurations
    parsers: Dict[str, ParserSettings] = Field(default_factory=dict, description="Parser settings")
    
    # Output settings
    output: OutputSettings = Field(default_factory=OutputSettings, description="Output configuration")
    
    # Logging settings
    logging: LoggingSettings = Field(default_factory=LoggingSettings, description="Logging configuration")
    
    # Processing options (from old project)
    hobl_enabled: bool = Field(False, description="Enable HOBL .PASS/.FAIL processing")
    folder_structure_detection: bool = Field(True, description="Auto-detect folder structure")
    power_picking_strategy: str = Field("MED", description="Power data selection strategy (MIN, MED, MAX)")
    inference_only_mode: bool = Field(False, description="Process only inference data")
    sort_similar_data: bool = Field(False, description="Sort similar datasets together")
    
    class Config:
        extra = "allow"  # Allow additional fields for future extensibility
    
    @validator('power_picking_strategy')
    def validate_power_strategy(cls, v):
        valid_strategies = ['MIN', 'MED', 'MAX']
        if v not in valid_strategies:
            raise ValueError(f"Power picking strategy must be one of: {valid_strategies}")
        return v


class ConfigurationManager:
    """Enhanced configuration manager with backward compatibility."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = Path(config_path) if config_path else None
        self.config = self._load_configuration()
    
    def _load_configuration(self) -> EnhancedParserConfig:
        """Load configuration from file or create default."""
        if self.config_path and self.config_path.exists():
            try:
                return self._load_from_file()
            except Exception as e:
                raise ConfigurationError(f"Failed to load configuration from {self.config_path}: {e}")
        else:
            return self._create_default_config()
    
    def _load_from_file(self) -> EnhancedParserConfig:
        """Load configuration from JSON or YAML file."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            if self.config_path.suffix.lower() in ['.yml', '.yaml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        # Handle old project configuration format
        if self._is_old_format(data):
            data = self._migrate_old_config(data)
        
        return EnhancedParserConfig(**data)
    
    def _is_old_format(self, data: Dict[str, Any]) -> bool:
        """Check if configuration is in old project format."""
        # Old format typically has direct DAQ target dictionary
        return (
            isinstance(data, dict) and
            any(key.startswith('P_') for key in data.keys()) and
            'version' not in data
        )
    
    def _migrate_old_config(self, old_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate old project configuration to new format."""
        migrated = {
            'version': '2.0.0',
            'description': 'Migrated from old project configuration',
            'daq_targets': {},
            'socwatch_targets': [],
            'pcie_targets': []
        }
        
        # Migrate DAQ targets
        for key, value in old_data.items():
            if key.startswith('P_') or key.startswith('V_') or key.startswith('I_'):
                migrated['daq_targets'][key] = {
                    'name': key,
                    'default_value': value if isinstance(value, (int, float)) else -1,
                    'unit': 'W' if key.startswith('P_') else 'V' if key.startswith('V_') else 'A',
                    'category': 'power' if key.startswith('P_') else 'voltage' if key.startswith('V_') else 'current'
                }
        
        return migrated
    
    def _create_default_config(self) -> EnhancedParserConfig:
        """Create default configuration with old project defaults."""
        # Default DAQ targets from old project
        default_daq = {
            "P_SSD": DAQTarget(name="P_SSD", default_value=-1, unit="W", category="power"),
            "V_VAL_VCC_PCORE": DAQTarget(name="V_VAL_VCC_PCORE", default_value=-1, unit="V", category="voltage"),
            "I_VAL_VCC_PCORE": DAQTarget(name="I_VAL_VCC_PCORE", default_value=-1, unit="A", category="current"),
            "V_VAL_VCC_ECORE": DAQTarget(name="V_VAL_VCC_ECORE", default_value=-1, unit="V", category="voltage"),
            "I_VAL_VCC_ECORE": DAQTarget(name="I_VAL_VCC_ECORE", default_value=-1, unit="A", category="current"),
            "V_VAL_VCCSA": DAQTarget(name="V_VAL_VCCSA", default_value=-1, unit="V", category="voltage"),
            "I_VAL_VCCSA": DAQTarget(name="I_VAL_VCCSA", default_value=-1, unit="A", category="current"),
            "V_VAL_VCCGT": DAQTarget(name="V_VAL_VCCGT", default_value=-1, unit="V", category="voltage"),
            "I_VAL_VCCGT": DAQTarget(name="I_VAL_VCCGT", default_value=-1, unit="A", category="current"),
            "P_VCC_PCORE": DAQTarget(name="P_VCC_PCORE", default_value=-1, unit="W", category="power"),
            "P_VCC_ECORE": DAQTarget(name="P_VCC_ECORE", default_value=-1, unit="W", category="power"),
            "P_VCCSA": DAQTarget(name="P_VCCSA", default_value=-1, unit="W", category="power"),
            "P_VCCGT": DAQTarget(name="P_VCCGT", default_value=-1, unit="W", category="power"),
            "P_VCCL2": DAQTarget(name="P_VCCL2", default_value=-1, unit="W", category="power"),
            "P_VCC1P8": DAQTarget(name="P_VCC1P8", default_value=-1, unit="W", category="power"),
            "P_VCCIO": DAQTarget(name="P_VCCIO", default_value=-1, unit="W", category="power"),
            "P_VCCDDRIO": DAQTarget(name="P_VCCDDRIO", default_value=-1, unit="W", category="power"),
            "P_VNNAON": DAQTarget(name="P_VNNAON", default_value=-1, unit="W", category="power"),
            "P_VNNAONLV": DAQTarget(name="P_VNNAONLV", default_value=-1, unit="W", category="power"),
            "P_VDDQ": DAQTarget(name="P_VDDQ", default_value=-1, unit="W", category="power"),
            "P_VDD2H": DAQTarget(name="P_VDD2H", default_value=-1, unit="W", category="power"),
            "P_VDD2L": DAQTarget(name="P_VDD2L", default_value=-1, unit="W", category="power"),
            "P_V1P8U_MEM": DAQTarget(name="P_V1P8U_MEM", default_value=-1, unit="W", category="power"),
            "P_SOC+MEMORY": DAQTarget(name="P_SOC+MEMORY", default_value=-1, unit="W", category="power"),
            "Run Time": DAQTarget(name="Run Time", default_value=-1, unit="s", category="time")
        }
        
        # Default Socwatch targets from old project
        default_socwatch = [
            SocwatchTarget(key="CPU_model", lookup="CPU native model", description="CPU model information"),
            SocwatchTarget(key="PCH_SLP50", lookup="PCH SLP-S0 State Summary: Residency (Percentage and Time)", description="PCH SLP-S0 state residency"),
            SocwatchTarget(key="S0ix_Substate", lookup="S0ix Substate Summary: Residency (Percentage and Time)", description="S0ix substate residency"),
            SocwatchTarget(key="PKG_Cstate", lookup="Platform Monitoring Technology CPU Package C-States Residency Summary: Residency (Percentage and Time)", description="CPU package C-state residency"),
            SocwatchTarget(key="Core_Cstate", lookup="Core C-State Summary: Residency (Percentage and Time)", description="Core C-state residency"),
            SocwatchTarget(key="Core_Concurrency", lookup="CPU Core Concurrency (OS)", description="CPU core concurrency"),
            SocwatchTarget(key="ACPI_Cstate", lookup="Core C-State (OS) Summary: Residency (Percentage and Time)", description="ACPI C-state residency"),
            SocwatchTarget(key="OS_wakeups", lookup="Processes by Platform Busy Duration", description="OS wakeup events"),
            SocwatchTarget(key="CPU-iGPU", lookup="CPU-iGPU Concurrency Summary: Residency (Percentage and Time)", description="CPU-iGPU concurrency"),
            SocwatchTarget(key="CPU_Pavr", lookup="CPU P-State Average Frequency (excluding CPU idle time)", description="CPU P-state average frequency"),
            SocwatchTarget(key="CPU_Pstate", lookup="CPU P-State/Frequency Summary: Residency (Percentage and Time)", description="CPU P-state residency"),
            SocwatchTarget(key="RC_Cstate", lookup="Integrated Graphics C-State  Summary: Residency (Percentage and Time)", description="Graphics C-state residency"),
            SocwatchTarget(key="DDR_BW", lookup="DDR Bandwidth Requests by Component Summary: Average Rate and Total", description="DDR bandwidth"),
            SocwatchTarget(key="IO_BW", lookup="IO Bandwidth Summary: Average Rate and Total", description="IO bandwidth"),
            SocwatchTarget(key="VC1_BW", lookup="Display VC1 Bandwidth Summary: Average Rate and Total", description="Display VC1 bandwidth"),
            SocwatchTarget(key="NPU_BW", lookup="Neural Processing Unit (NPU) to Memory Bandwidth Summary: Average Rate and Total", description="NPU bandwidth"),
            SocwatchTarget(key="Media_BW", lookup="Media to Network on Chip (NoC) Bandwidth Summary: Average Rate and Total", description="Media bandwidth"),
            SocwatchTarget(key="IPU_BW", lookup="Image Processing Unit (IPU) to Network on Chip (NoC) Bandwidth Summary: Average Rate and Total", description="IPU bandwidth"),
            SocwatchTarget(key="CCE_BW", lookup="CCE to Network on Chip (NoC) Bandwidth Summary: Average Rate and Total", description="CCE bandwidth"),
            SocwatchTarget(key="GT_BW", lookup="Chip GT Bandwidth Summary: Average Rate and Total", description="GT bandwidth"),
            SocwatchTarget(key="D2D_BW", lookup="Chip Die to Die Bandwidth Summary: Average Rate and Total", description="Die-to-die bandwidth"),
            SocwatchTarget(key="CPU_temp", lookup="Temperature Metrics Summary - Sampled: Min/Max/Avg", description="CPU temperature"),
            SocwatchTarget(key="SoC_temp", lookup="SoC Domain Temperatures Summary - Sampled: Min/Max/Avg", description="SoC temperature"),
            SocwatchTarget(key="NPU_Dstate", lookup="Neural Processing Unit (NPU) D-State Residency Summary: Residency (Percentage and Time)", description="NPU D-state residency"),
            SocwatchTarget(key="PMC+SLP_S0", lookup="PCH Active State (as percentage of PMC Active plus SLP_S0 Time) Summary: Residency (Percentage)", description="PCH active state"),
            SocwatchTarget(key="DC_count", lookup="Dynamic Display State Enabling", description="Dynamic display state"),
            SocwatchTarget(key="Media_Cstate", lookup="Media C-State Residency Summary: Residency (Percentage and Time)", description="Media C-state residency"),
            SocwatchTarget(key="NPU_Pstate", lookup="Neural Processing Unit (NPU) P-State Summary - Sampled: Approximated Residency (Percentage)", buckets=["0", "1900", "1901-2900", "2901-3899", "3900"], description="NPU P-state with bucketing"),
            SocwatchTarget(key="MEMSS_Pstate", lookup="Memory Subsystem (MEMSS) P-State Summary - Sampled: Approximated Residency (Percentage)", description="Memory subsystem P-state"),
            SocwatchTarget(key="NoC_Pstate", lookup="Network on Chip (NoC) P-State Summary - Sampled: Approximated Residency (Percentage)", buckets=["400", "401-1049", "1050"], description="NoC P-state with bucketing"),
            SocwatchTarget(key="iGFX_Pstate", lookup="Integrated Graphics P-State/Frequency Summary - Sampled: Approximated Residency (Percentage)", buckets=["0", "400", "401-1799", "1800-2049", "2050"], description="iGFX P-state with bucketing")
        ]
        
        # Default PCIe targets from old project
        default_pcie = [
            PCIeTarget(key="PCIe_LPM", devices=["NVM"], lookup="PCIe LPM Summary - Sampled: Approximated Residency (Percentage)", description="PCIe Low Power Mode"),
            PCIeTarget(key="PCIe_Active", devices=["NVM"], lookup="PCIe Link Active Summary - Sampled: Approximated Residency (Percentage)", description="PCIe Link Active"),
            PCIeTarget(key="PCIe_LTRsnoop", devices=["NVM"], lookup="PCIe LTR Snoop Summary - Sampled: Histogram", description="PCIe LTR Snoop")
        ]
        
        # Default parser settings
        default_parsers = {
            "power": ParserSettings(enabled=True, priority=10, options={"daq_targets": default_daq, "average_column": "Average"}),
            "power_trace": ParserSettings(enabled=True, priority=15, options={"sample_rate": 1000, "max_samples": 100000}),
            "etl": ParserSettings(enabled=True, priority=20, options={"max_events": 10000}),
            "model_output": ParserSettings(enabled=True, priority=25, options={}),
            "socwatch": ParserSettings(enabled=True, priority=30, options={"socwatch_targets": default_socwatch}),
            "pcie": ParserSettings(enabled=True, priority=35, options={"pcie_targets": default_pcie}),
            "hobl": ParserSettings(enabled=False, priority=5, options={"hobl_enabled": False})
        }
        
        return EnhancedParserConfig(
            daq_targets=default_daq,
            socwatch_targets=default_socwatch,
            pcie_targets=default_pcie,
            parsers=default_parsers
        )
    
    def save_configuration(self, output_path: Optional[Union[str, Path]] = None) -> None:
        """Save current configuration to file."""
        save_path = Path(output_path) if output_path else self.config_path
        
        if not save_path:
            raise ConfigurationError("No output path specified for saving configuration")
        
        # Convert to dictionary for serialization
        config_dict = self.config.dict()
        
        # Save as JSON or YAML based on extension
        with open(save_path, 'w', encoding='utf-8') as f:
            if save_path.suffix.lower() in ['.yml', '.yaml']:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_dict, f, indent=2, default=str)
    
    def get_parser_config(self, parser_name: str) -> Optional[ParserSettings]:
        """Get configuration for specific parser."""
        return self.config.parsers.get(parser_name)
    
    def get_enabled_parsers(self) -> List[str]:
        """Get list of enabled parser names."""
        return [name for name, settings in self.config.parsers.items() if settings.enabled]
    
    def get_daq_targets(self) -> Dict[str, DAQTarget]:
        """Get DAQ target configuration."""
        return self.config.daq_targets
    
    def get_socwatch_targets(self) -> List[SocwatchTarget]:
        """Get Socwatch target configuration."""
        return self.config.socwatch_targets
    
    def get_pcie_targets(self) -> List[PCIeTarget]:
        """Get PCIe target configuration."""
        return self.config.pcie_targets
    
    def update_parser_config(self, parser_name: str, **kwargs) -> None:
        """Update parser configuration."""
        if parser_name not in self.config.parsers:
            self.config.parsers[parser_name] = ParserSettings()
        
        current_config = self.config.parsers[parser_name]
        for key, value in kwargs.items():
            if hasattr(current_config, key):
                setattr(current_config, key, value)
            else:
                current_config.options[key] = value
    
    @property
    def logging_config(self) -> LoggingSettings:
        """Get logging configuration."""
        return self.config.logging
    
    @property
    def output_config(self) -> OutputSettings:
        """Get output configuration."""
        return self.config.output
    
    @property
    def hobl_enabled(self) -> bool:
        """Check if HOBL processing is enabled."""
        return self.config.hobl_enabled
    
    @property
    def power_picking_strategy(self) -> str:
        """Get power picking strategy."""
        return self.config.power_picking_strategy