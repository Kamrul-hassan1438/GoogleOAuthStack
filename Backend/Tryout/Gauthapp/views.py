from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers import UserSerializer
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from decouple import config
import logging
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)

class GoogleLoginAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            logger.debug(f"Received request data: {request.data}")
            code = request.data.get('code')
            
            if not code:
                logger.error("No authorization code provided")
                return Response(
                    {'error': 'Authorization code is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify the ID token with clock skew tolerance
            client_id = config('GOOGLE_CLIENT_ID')
            logger.debug(f"Verifying ID token with client_id: {client_id}")
            idinfo = id_token.verify_oauth2_token(
                code,
                google_requests.Request(),
                client_id,
                clock_skew_in_seconds=10  # Allow 10 seconds of clock skew
            )
            logger.debug(f"ID token verified: {idinfo}")

            # Extract user info
            email = idinfo['email']
            google_id = idinfo['sub']

            # Find or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': idinfo.get('given_name', ''),
                    'last_name': idinfo.get('family_name', '')
                }
            )

            # Link social account if not already linked
            if created or not SocialAccount.objects.filter(user=user, provider='google').exists():
                SocialAccount.objects.create(
                    user=user,
                    provider='google',
                    uid=google_id,
                    extra_data=idinfo
                )
                logger.debug(f"Created social account for user: {user.username}")

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Serialize user data
            serializer = UserSerializer(user)
            return Response({
                'user': serializer.data,
                'message': 'Successfully logged in',
                'access_token': access_token,
                'refresh_token': refresh_token
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.error(f"Invalid token: {str(e)}")
            return Response(
                {'error': f'Invalid token: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"Unexpected error: {str(e)}")
            return Response(
                {'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        