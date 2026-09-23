from django.db import migrations, models


class Migration(migrations.Migration):
    # Restores the migration that 0027 depends on; the fields were added to
    # AssociationFilingStatus in commit 3b5c7f8 but the migration file was never committed.

    dependencies = [
        ('tax_form', '0025_add_state_local_taxes'),
    ]

    operations = [
        migrations.AddField(
            model_name='associationfilingstatus',
            name='invoice_sent_date',
            field=models.DateField(blank=True, help_text='Date the invoice was sent', null=True),
        ),
        migrations.AddField(
            model_name='associationfilingstatus',
            name='payment_received_date',
            field=models.DateField(blank=True, help_text='Date payment was received', null=True),
        ),
    ]
