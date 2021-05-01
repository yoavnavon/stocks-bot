include .env
export

set-hook:
	curl https://api.telegram.org/bot${TOKEN}/setWebHook?url=${WEBHOOK_URL}

delete-hook:
	curl https://api.telegram.org/bot${TOKEN}/deleteWebhook