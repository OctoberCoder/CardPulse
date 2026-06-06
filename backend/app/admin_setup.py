from sqlalchemy import create_engine
from sqladmin import Admin, ModelView
from app.config import get_settings
from app.models.user import User
from app.models.card import CardBrand, Denomination, CardSubmission
from app.models.wallet import Wallet, WalletTransaction

settings = get_settings()
engine = create_engine(settings.database_url_sync)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.phone, User.tier, User.kyc_status, User.is_active, User.is_staff, User.created_at]
    column_searchable_list = [User.email, User.phone]
    column_sortable_list = [User.id, User.created_at]
    form_excluded_columns = [User.password_hash]


class CardBrandAdmin(ModelView, model=CardBrand):
    column_list = [CardBrand.id, CardBrand.name, CardBrand.slug, CardBrand.active, CardBrand.created_at]
    column_searchable_list = [CardBrand.name]


class DenominationAdmin(ModelView, model=Denomination):
    column_list = [Denomination.id, Denomination.brand, Denomination.value, Denomination.currency, Denomination.active]


class CardSubmissionAdmin(ModelView, model=CardSubmission):
    column_list = [
        CardSubmission.id, CardSubmission.user, CardSubmission.brand, CardSubmission.denomination,
        CardSubmission.quoted_amount, CardSubmission.final_amount, CardSubmission.status,
        CardSubmission.submitted_at,
    ]
    column_searchable_list = [CardSubmission.admin_notes]
    form_excluded_columns = [CardSubmission.card_code]


class WalletAdmin(ModelView, model=Wallet):
    column_list = [Wallet.id, Wallet.user, Wallet.balance, Wallet.currency, Wallet.locked_amount]


class WalletTransactionAdmin(ModelView, model=WalletTransaction):
    column_list = [WalletTransaction.id, WalletTransaction.wallet, WalletTransaction.type,
                   WalletTransaction.amount, WalletTransaction.reference, WalletTransaction.created_at]


def setup_admin(app):
    admin = Admin(app, engine)
    admin.add_view(UserAdmin)
    admin.add_view(CardBrandAdmin)
    admin.add_view(DenominationAdmin)
    admin.add_view(CardSubmissionAdmin)
    admin.add_view(WalletAdmin)
    admin.add_view(WalletTransactionAdmin)
    return admin
