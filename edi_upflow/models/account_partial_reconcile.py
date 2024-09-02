# Copyright 2023 Foodles (https://www.foodles.com/)
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, fields, models


class AccountPartialReconcile(models.Model):
    _name = "account.partial.reconcile"
    _inherit = [
        "account.partial.reconcile",
        "mail.thread",
        "edi.exchange.consumer.mixin",
    ]

    sent_to_upflow = fields.Boolean(
        default=False,
        help="Technical field to know if the record has been synchronized with upflow",
    )

    def unlink(self):
        odoobot = self.env.ref("base.partner_root")
        message_body = _("This job has been canceled and its associated EDI exchange was deleted "
                         "because the associated reconciliation was deleted")

        exchanges_to_delete = self.exchange_record_ids.filtered(
            lambda exchange: exchange.edi_exchange_state == "new"
        )
        for exchange_to_delete in exchanges_to_delete:
            exchange_to_delete.unlink()
            queue_jobs_to_cancel = self.env["queue.job"].search([
                ("job_function_id.channel_id", "=", self.env.ref("edi_oca.channel_edi_exchange").id),
                ("func_string", "like", str(exchange_to_delete)),
                ("state", "=", "pending"),
            ])
            if not queue_jobs_to_cancel:
                continue
            queue_jobs_to_cancel.button_cancelled()
            queue_jobs_to_cancel.message_post(
                body=message_body,
                message_type="comment",
                subtype_xmlid="mail.mt_note",
                author_id=odoobot.id
            )
        return super().unlink()
