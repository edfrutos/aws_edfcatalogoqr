const mongoose = require('mongoose');

const UserSchema = new mongoose.Schema(
    {
        username: {
            type: String,
            required: true,
            unique: true,
        },
        email: {
            type: String,
            required: true,
            unique: true,
        },
        password: {
            type: String,
            required: true,
        },
        image_file: {
            // Nuevo campo para la foto de perfil
            type: String,
            default: '', // Valor por defecto vacío
        },
    },
    { timestamps: true },
);

module.exports = mongoose.model('User', UserSchema);
