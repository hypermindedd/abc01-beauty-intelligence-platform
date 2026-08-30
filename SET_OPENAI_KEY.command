#!/bin/bash
set -e
cd "$(dirname "$0")"
echo ""
echo "ABC.DEMO.02 — Local API configuration"
echo "کلید API فقط روی همین Mac و داخل فایل .env.local ذخیره می‌شود."
echo "کلید را داخل ChatGPT ارسال نکنید."
echo ""
read -s -p "OPENAI_API_KEY: " KEY
echo ""
if [ -z "$KEY" ]; then
  echo "کلید خالی بود؛ تغییری انجام نشد."
  exit 1
fi
cat > .env.local <<EOF
OPENAI_API_KEY=$KEY
ABC_TEXT_MODEL=gpt-5.6-terra
ABC_IMAGE_MODEL=gpt-image-2
ABC_TEXT_REASONING=low
ABC_IMAGE_QUALITY=high
ABC_LIVE_TEXT=1
ABC_LIVE_VISUAL=1
ABC_SESSION_PERSISTENCE=1
ABC_VISUAL_MAX_ATTEMPTS=2
EOF
chmod 600 .env.local
echo ""
echo "LIVE provider configuration saved locally."
echo "حالا START_ABC_LIVE_DEMO.command را اجرا کنید."
echo ""
read -n 1 -s -r -p "Press any key to close..."
