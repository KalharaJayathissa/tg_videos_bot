conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASKING_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input)],
        },
        fallbacks=[],
    )