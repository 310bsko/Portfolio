from django import forms

from .models import Message


class FormulaireContact(forms.ModelForm):
    # Champ piège (honeypot) : invisible pour un humain, rempli par les robots.
    site_web = forms.CharField(required=False, label="Ne pas remplir ce champ")

    class Meta:
        model = Message
        fields = ["nom", "email", "sujet", "contenu"]
        labels = {"nom": "Nom", "email": "Email", "sujet": "Sujet", "contenu": "Message"}
        widgets = {
            "nom": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "contenu": forms.Textarea(attrs={"rows": 6, "maxlength": 5000}),
        }

    def clean_contenu(self):
        contenu = self.cleaned_data["contenu"].strip()
        if len(contenu) < 10:
            raise forms.ValidationError("Votre message est un peu court (10 caractères minimum).")
        if len(contenu) > 5000:
            raise forms.ValidationError("Votre message dépasse 5000 caractères.")
        return contenu

    @property
    def est_un_robot(self):
        return bool(self.data.get("site_web", "").strip())
