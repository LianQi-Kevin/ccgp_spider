from pydantic import BaseModel, Field


class ContractModel(BaseModel):
    contract_id: str = Field(default=None, alias='合同编号')
    contract_name: str = Field(default=None, alias='合同名称')
    project_id: str = Field(default=None, alias='项目编号')
    project_name: str = Field(default=None, alias='项目名称')
    purchaser: str = Field(default=None, alias='合同主体_采购人（甲方）')
    purchaser_address: str = Field(default=None, alias='合同主体_地址')
    purchaser_contact: str = Field(default=None, alias='合同主体_联系方式')
    supplier: str = Field(default=None, alias='合同主体_供应商（乙方）')
    supplier_address: str = Field(default=None, alias='合同主体_地址_2')
    supplier_contact: str = Field(default=None, alias='合同主体_联系方式_2')
    item_name: str = Field(default=None, alias='合同主要信息_主要标的名称')
    specifications: str = Field(default=None, alias='合同主要信息_规格型号（或服务要求）')
    quantity: str = Field(default=None, alias='合同主要信息_主要标的数量')
    unit_price: str = Field(default=None, alias='合同主要信息_主要标的单价')
    contract_amount: str = Field(default=None, alias='合同主要信息_合同金额')
    performance_info: str = Field(default=None, alias='合同主要信息_履约期限、地点等简要信息')
    procurement_method: str = Field(default=None, alias='合同主要信息_采购方式')
    contract_sign_date: str = Field(default=None, alias='合同签订日期')
    contract_announce_date: str = Field(default=None, alias='合同公告日期')
    attachment_filename: str = Field(default=None, alias='附件_filename')
    attachment_link: str = Field(default=None, alias='附件_href')
    winning_bid_filename: str = Field(default=None, alias='中标合同_filename')
    winning_bid_link: str = Field(default=None, alias='中标合同_href')


class ConversionOldContractModel(ContractModel):
    purchaser: str = Field(default=None, alias='采购人(甲方)')
    supplier: str = Field(default=None, alias='供应商(乙方)')
    purchaser_address: str = Field(default=None, alias='所属地域')
    supplier_address: str = Field(default=None, alias='所属地域')
    contract_amount: str = Field(default=None, alias='合同金额')
    attachment_filename: str = Field(default=None, alias='合同附件_filename')
    attachment_link: str = Field(default=None, alias='合同附件_href')
    winning_bid_filename: str = Field(default=None, alias='中标、成交公告_filename')
    winning_bid_link: str = Field(default=None, alias='中标、成交公告_href')


class MainContractModel(ContractModel):
    signing_date: str = Field(default=None, description='签订日期')
    contract_URL: str = Field(default=None, description='子页面URL')
    contract_title: str = Field(default=None, description='合同标题')
    publish_date: str = Field(default=None, description='发布时间')
