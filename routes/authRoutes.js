const express = require('express');
const router = express.Router();
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const User = require('../models/User'); // Asegúrate de que tienes un modelo User

// Registro de usuario
router.post('/register', async (req, res) => {
    try {
        const hashedPassword = await bcrypt.hash(req.body.password, 10);
        const user = new User({
            username: req.body.username,
            password: hashedPassword
        });
        const newUser = await user.save();
        res.status(201).json(newUser);
    } catch (err) {
        res.status(400).json({ message: err.message });
    }
});

// Login de usuario
router.post('/login', async (req, res) => {
    try {
        const user = await User.findOne({ username: req.body.username });
        if (user && await bcrypt.compare(req.body.password, user.password)) {
            const token = jwt.sign({ _id: user._id }, process.env.JWT_SECRET, { expiresIn: '1h' });
            res.json({ token });
        } else {
            res.status(400).json({ message: 'Usuario o contraseña incorrectos' });
        }
    } catch (err) {
        res.status(500).json({ message: err.message });
    }
});

module.exports = router;

router.post('/forgot-password', async (req, res) => {
    const { email } = req.body;

    if (!email) {
        return res.status(400).json({ message: 'El campo de correo electrónico es obligatorio' });
    }

    try {
        const user = await User.findOne({ email });
        if (!user) {
            return res.status(400).json({ message: 'Correo no registrado' });
        }

        // Aquí puedes añadir la lógica para enviar un correo de recuperación de contraseña

        res.status(200).json({ message: 'Se ha enviado un correo de recuperación de contraseña' });
    } catch (error) {
        res.status(500).json({ message: 'Error al recuperar la contraseña' });
    }
});

module.exports = router;