# sms/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from scraapy.permissions import IsBusiness, IsStaff,IsBusinessOrIsStaff
from rest_framework import viewsets


from django.contrib.auth import get_user_model
from .models import OrderScrap


from sms.serializers import ScrapItemSerializer,OrderScrapReadSerializer
from sms.utils import send_order_approved_email


User = get_user_model()


class ScrapItemCreateAPIView(APIView):
    """
    POST /api/sms/create-scrap-item/
    Accepte :
      - JSON (avec images encodées en Base64)  -> via JSONParser
      - ou Multipart/Form-Data (fichiers physiques) -> via MultiPartParser et FormParser

    Exemple de JSON attendu (Body → Raw → application/json) :

    {
      "email": "anis@example.com",
      "user_type": "individual",
      "pickup_address": "26.43722, 49.99741",
      "phone": "0544284596",
      "banking_info": {
        "full_name": "Anis Gouadria",
        "bank_name": "Saudi National Bank",
        "iban_number": "SA1230000045621345678904"
      },
      "category_group": 36,
      "name": "Office paper (white/colored)",
      "size": "1200",
      "quantity": 700,
      "description": "No description provided",
      "status": "pending",
      "images": [
        {
          "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD…(Base64 complet)…"
        }
      ]
    }

    Exemple Multipart/Form-Data (Body → form-data) :
      • email                (Text)   anis@example.com
      • user_type            (Text)   individual
      • pickup_address       (Text)   26.43722, 49.99741
      • phone                (Text)   0544284596
      • banking_info.full_name    (Text)   Anis Gouadria
      • banking_info.bank_name    (Text)   Saudi National Bank
      • banking_info.iban_number  (Text)   SA1230000045621345678904
      • category_group       (Text)   36
      • name                 (Text)   Office paper (white/colored)
      • size                 (Text)   1200
      • quantity             (Text)   700
      • description          (Text)   No description provided
      • status               (Text)   pending
      • images               (File)   (sélectionnez un fichier image.jpg)
    """

    parser_classes = [JSONParser, MultiPartParser, FormParser]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ScrapItemSerializer(data=request.data)
        if serializer.is_valid():
            scrap_item = serializer.save()
            return Response(
                {
                    "scrap_item_id": scrap_item.id,
                    "order_id": scrap_item.order.id
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class OrderScrapViewSet(viewsets.ModelViewSet):
    """
    Vue pour récupérer les commandes et leurs éléments de scrap, accessibles seulement aux utilisateurs `IsStaff`.
    """
    queryset = OrderScrap.objects.all()
    serializer_class = OrderScrapReadSerializer
    permission_classes = [IsStaff]


    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_status = instance.status

        # Mise à jour de l'instance via le serializer
        response = super().update(request, *args, **kwargs)

        # Rafraîchir les données depuis la base pour voir les nouvelles valeurs
        instance.refresh_from_db()

        # Si le statut est passé à 'APPROVED', envoyer l'email
        if old_status != 'APPROVED' and instance.status == 'APPROVED':
            send_order_approved_email(instance)

        return response

    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        """
        Récupérer toutes les commandes d'un utilisateur, avec les ScrapItems et informations bancaires.
        Accessible uniquement aux utilisateurs staff.
        """
        try:
            user = User.objects.get(id=pk)
            orders = OrderScrap.objects.filter(user=user)
            serializer = self.get_serializer(orders, many=True)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur non trouvé.'}, status=404)