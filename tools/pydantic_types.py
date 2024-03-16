from typing import Optional

from pydantic import BaseModel, Field


class ContractMainSubject(BaseModel):
    purchaser_name: Optional[str] = Field(default=None, description="采购人(甲方)")
    purchaser_address: Optional[str] = Field(default=None, description="采购人地址")
    purchaser_contact: Optional[str] = Field(default=None, description="采购人联系方式")
    supplier_name: Optional[str] = Field(default=None, description="供应商(乙方)")
    supplier_address: Optional[str] = Field(default=None, description="供应商地址")
    supplier_contact: Optional[str] = Field(default=None, description="供应商联系方式")


class ContractMainInfo(BaseModel):
    main_object_name: Optional[str] = Field(default=None, description="主要标的名称")
    specification_or_service_requirement: Optional[str] = Field(default=None, description="规格型号(或服务要求)")
    main_object_quantity: Optional[str] = Field(default=None, description="主要标的数量")
    main_object_unit_price: Optional[str] = Field(default=None, description="主要标的单价")
    contract_amount: Optional[str] = Field(default=None, description="合同金额")
    performance_info: Optional[str] = Field(default=None, description="履约期限、地点等简要信息")
    procurement_method: Optional[str] = Field(default=None, description="采购方式")


class ContractAnnouncementDetails(BaseModel):
    contract_id: Optional[str] = Field(default=None, description="合同编号")
    contract_name: Optional[str] = Field(default=None, description="合同名称")
    project_id: Optional[str] = Field(default=None, description="项目编号")
    contract_main_subject: Optional[ContractMainSubject] = Field(default=None, description="合同主体")
    contract_main_info: Optional[ContractMainInfo] = Field(default=None, description="合同主要信息")
    contract_sign_date: Optional[str] = Field(default=None, description="合同签订日期")
    contract_announcement_date: Optional[str] = Field(default=None, description="合同公告日期")
    winning_bid_announcement_name: Optional[str] = Field(default=None, description="中标合同名称")
    winning_bid_announcement_link: Optional[str] = Field(default=None, description="中标公告链接")
    attachments: Optional[str] = Field(default=None, description="附件")
